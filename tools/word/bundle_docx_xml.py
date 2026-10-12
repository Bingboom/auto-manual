from __future__ import annotations

from io import BytesIO
import re
from xml.etree import ElementTree as ET

_XMLNS_DECL_RE = re.compile(r'\sxmlns(?::(?P<prefix>[-A-Za-z0-9_.]+))?="[^"]+"')


def collect_xml_namespaces(xml_payload: bytes) -> dict[str, str]:
    namespaces: dict[str, str] = {}
    for _event, ns_decl in ET.iterparse(BytesIO(xml_payload), events=("start-ns",)):
        prefix, uri = ns_decl
        namespaces.setdefault(prefix or "", uri)
    return namespaces


def inject_missing_namespace_declarations(xml_payload: bytes, namespaces: dict[str, str]) -> bytes:
    if not namespaces:
        return xml_payload

    xml_text = xml_payload.decode("utf-8")
    search_from = 0
    if xml_text.startswith("<?xml"):
        decl_end = xml_text.find("?>")
        if decl_end != -1:
            search_from = decl_end + 2

    root_start = xml_text.find("<", search_from)
    root_end = xml_text.find(">", root_start + 1)
    if root_start == -1 or root_end == -1:
        return xml_payload

    root_open = xml_text[root_start:root_end]
    existing_prefixes = {match.group("prefix") or "" for match in _XMLNS_DECL_RE.finditer(root_open)}

    additions: list[str] = []
    for prefix, uri in namespaces.items():
        if prefix in existing_prefixes:
            continue
        escaped_uri = uri.replace("&", "&amp;").replace('"', "&quot;")
        if prefix:
            additions.append(f' xmlns:{prefix}="{escaped_uri}"')
        else:
            additions.append(f' xmlns="{escaped_uri}"')

    if not additions:
        return xml_payload

    xml_text = f"{xml_text[:root_end]}{''.join(additions)}{xml_text[root_end:]}"
    return xml_text.encode("utf-8")


def serialize_xml_preserving_namespaces(root: ET.Element, *, original_xml: bytes) -> bytes:
    namespaces = collect_xml_namespaces(original_xml)
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)
    serialized = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return inject_missing_namespace_declarations(serialized, namespaces)
