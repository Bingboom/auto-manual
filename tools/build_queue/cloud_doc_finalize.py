"""Make a bot-created Feishu cloud doc usable by the operator.

The build/publish queue imports the review/publish cloud doc as the **bot**
(`FEISHU_PHASE2_IDENTITY=bot` in the workflows), so the operator who requested
the build cannot edit it — they can only make a 副本. These ops run right after
the import:

1. **Grant edit access** — add the operator (their `operator_union_id` from the
   `文档构建表`) as a ``full_access`` collaborator. The bot stays the owner, so
   rebuilds/overwrites keep working.
2. **Wiki co-location** — move the cloud doc into the same wiki node as the Word
   artifact, so the editable doc and the Word sit together.

Both are **best-effort**: a failure logs a warning and never fails the build
(the doc is already created). The Feishu app needs the
``drive:permission.member:create`` scope for the grant to take effect live.
"""

from __future__ import annotations

import json
from typing import Any, Callable


def grant_doc_full_access(
    *,
    cli_bin: str,
    identity: str,
    doc_token: str,
    member_id: str,
    run_lark_cli_json: Callable[..., dict[str, Any]],
    doc_type: str = "docx",
    member_type: str = "unionid",
    perm: str = "full_access",
) -> dict[str, Any]:
    """Grant a collaborator ``perm`` on a cloud doc the bot owns."""
    if not doc_token:
        raise RuntimeError("grant_doc_full_access requires a doc_token")
    if not member_id:
        raise RuntimeError("grant_doc_full_access requires a member_id")
    return run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "drive",
            "permission.members",
            "create",
            "--as",
            identity,
            "--yes",
            "--params",
            json.dumps({"token": doc_token, "type": doc_type}, ensure_ascii=False, separators=(",", ":")),
            "--data",
            json.dumps(
                {"member_type": member_type, "member_id": member_id, "perm": perm},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        ],
    )


def is_wiki_destination(destination: Any) -> bool:
    """True when ``destination`` carries a wiki space + parent node (move target)."""
    return bool(
        getattr(destination, "space_id", "") and getattr(destination, "parent_wiki_token", "")
    )


def resolve_cloud_doc_grantee(*, operator_union_id: str = "", default_editor: str = "") -> tuple[str, str]:
    """Pick who to grant edit access to: ``(member_id, member_type)``.

    Prefer the build row's operator (a union id). Fall back to a configured default
    editor (``FEISHU_CLOUD_DOC_DEFAULT_EDITOR``) when the row has no operator — the
    common case today, since that column is universally unpopulated. Returns
    ``("", "")`` when neither is set (the grant is then skipped).

    The default editor may carry an explicit type (``openid:ou_x`` / ``unionid:on_x``)
    or be a bare id whose type is inferred from its prefix (``ou_`` -> openid,
    ``on_`` -> unionid, anything else -> openid).
    """
    operator = (operator_union_id or "").strip()
    if operator:
        return operator, "unionid"
    spec = (default_editor or "").strip()
    if not spec:
        return "", ""
    if ":" in spec:
        mtype, _, mid = spec.partition(":")
        if mtype.strip() and mid.strip():
            return mid.strip(), mtype.strip()
        spec = (mid or mtype).strip()
    if spec.startswith("on_"):
        return spec, "unionid"
    return spec, "openid"


def finalize_cloud_doc(
    *,
    cloud_doc_token: str,
    cloud_doc_url: str,
    grantee_member_id: str,
    grantee_member_type: str,
    destination: Any,
    grant_full_access: Callable[..., Any],
    move_to_wiki: Callable[..., str],
    on_warning: Callable[[str], None] | None = None,
) -> str:
    """Grant the resolved grantee edit access + co-locate the doc in the Word's wiki node.

    The grantee is ``(grantee_member_id, grantee_member_type)`` from
    :func:`resolve_cloud_doc_grantee` (the build-row operator, else a configured
    default editor). Best-effort: a failed grant/move logs a warning and never fails
    the build. Returns the doc URL — the wiki URL after a successful move, else the
    original import URL (still edit-granted).
    """
    def _warn(message: str) -> None:
        if on_warning is not None:
            on_warning(message)

    if grantee_member_id:
        try:
            grant_full_access(
                doc_token=cloud_doc_token,
                member_id=grantee_member_id,
                member_type=grantee_member_type,
            )
        except Exception as exc:  # noqa: BLE001 - best-effort; never fail the build
            _warn(f"cloud-doc edit-access grant failed for {cloud_doc_token}: {exc}")

    if is_wiki_destination(destination):
        try:
            return move_to_wiki(obj_token=cloud_doc_token, doc_url=cloud_doc_url)
        except Exception as exc:  # noqa: BLE001 - best-effort; keep the import URL
            _warn(f"cloud-doc wiki co-location failed for {cloud_doc_token}: {exc}")
    return cloud_doc_url
