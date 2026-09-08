"""Optional OSS SDK adapter; credentials and SDK runtime stay outside Git."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_prefix(value: str) -> str:
    if not value or "\\" in value or any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("Invalid OSS prefix")
    return value + "/"


def upload_archive(release: Path, bucket: object, prefix: str) -> dict:
    """Preflight every object, reserve the manifest identity, then verify bytes.

    The reservation prevents concurrent, different releases mixing in one prefix.
    A failed run may leave partial objects; completion is a separate marker.
    Retries must use the original frozen local package, not a new PDF render.
    """
    from tools.safe_copy import assert_source_tree_no_symlinks
    from tools.web_archive_package import relative_file
    from tools.web_manual_package import safe_segment

    assert_source_tree_no_symlinks(release, label="OSS archive")
    manifest_path = release / "release-manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema_version") != "web-oss-archive/v1":
        raise ValueError("Unsupported OSS archive manifest")
    model = safe_segment(manifest["model"])
    version = safe_segment(manifest["version"])
    safe_segment(manifest["region"])
    base = checked_prefix(prefix) + f"products/{model}/releases/{version}/"
    entries = manifest["files"]
    names = [entry['path'] for entry in entries]
    if len(set(names)) != len(names) or any(n.startswith("_archive-") or n == "release-manifest.json" for n in names):
        raise ValueError("Duplicate or reserved archive file")
    for entry in entries:
        p = relative_file(release, entry['path'])
        if p.stat().st_size != entry['bytes'] or sha(p.read_bytes()) != entry['sha256']:
            raise ValueError("Local archive checksum mismatch")
    expected = set(names) | {"release-manifest.json"}
    if {p.relative_to(release).as_posix() for p in release.rglob('*') if p.is_file()} != expected:
        raise ValueError("Unmanifested archive files")
    payloads = [(name, release / name) for name in names] + [("release-manifest.json", manifest_path)]

    def existing_matches(name: str, data: bytes) -> bool:
        key = base + name
        if bucket.object_exists(key):
            if sha(bucket.get_object(key).read()) != sha(data):
                raise ValueError("Immutable OSS archive conflict: " + name)
            return True
        return False

    # All conflicts are checked before the first mutation.
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda item: existing_matches(item[0], item[1].read_bytes()), payloads))
    reservation = "_archive-reservation.json"
    if not existing_matches(reservation, manifest_bytes):
        try:
            bucket.put_object(base + reservation, manifest_bytes, headers={"x-oss-forbid-overwrite": "true"})
        except Exception:
            if not existing_matches(reservation, manifest_bytes):
                raise

    def put_verified(name: str, data: bytes) -> None:
        import mimetypes
        if not existing_matches(name, data):
            headers = {"x-oss-forbid-overwrite": "true", "x-oss-meta-sha256": sha(data),
                       "Content-Type": mimetypes.guess_type(name)[0] or "application/octet-stream"}
            try:
                bucket.put_object(base + name, data, headers=headers)
            except Exception:
                if not existing_matches(name, data):
                    raise
        if sha(bucket.get_object(base + name).read()) != sha(data):
            raise ValueError("Remote archive checksum mismatch: " + name)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda item: put_verified(item[0], item[1].read_bytes()), payloads[:-1]))
    put_verified("release-manifest.json", manifest_bytes)
    receipt = {"schema_version": "web-oss-archive-complete/v1", "manifest_sha256": sha(manifest_bytes),
               "verified_files": len(payloads)}
    put_verified("_archive-complete.json", json.dumps(receipt, sort_keys=True).encode())
    return {"status": "archived", "prefix": base, **receipt}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--settings", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        import oss2
        settings = json.loads(args.settings.read_text(encoding="utf-8"))
        credentials = Path(settings["credentials_file"]).expanduser()
        if os.name != "nt" and credentials.stat().st_mode & 0o077:
            raise ValueError("Credentials file must be owner-only")
        cfg = json.loads(credentials.read_text(encoding="utf-8"))
        if not cfg['endpoint'].startswith('https://'):
            raise ValueError("OSS endpoint must use HTTPS")
        bucket = oss2.Bucket(oss2.AuthV4(cfg['access_key_id'], cfg['access_key_secret']),
                             cfg['endpoint'], cfg['bucket'], region=cfg['region'])
        report = upload_archive(args.release, bucket, settings['prefix'])
        report['bucket'] = cfg['bucket']
    except Exception as exc:
        # SDK exception strings can contain request credentials. Never serialize them.
        report = {"status": "failed", "error_type": type(exc).__name__}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OSS archive: " + report['status'])
    if report['status'] != 'archived':
        raise SystemExit(1)


if __name__ == "__main__":
    main()
