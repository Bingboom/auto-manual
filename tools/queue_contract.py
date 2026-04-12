from __future__ import annotations

from dataclasses import dataclass
from typing import Any

TRIGGER_FIELD = "\u662f\u5426\u89e6\u53d1\u6587\u6863\u6784\u5efa"
LEGACY_TRIGGER_FIELDS = ("\u662f\u5426\u6784\u5efa\u6587\u6863\uff1f",)
RESULT_FIELD = "\u6784\u5efa\u7ed3\u679c"
DOCUMENT_ID_FIELD = "Document_ID"
DOCUMENT_KEY_FIELD = "Document_Key"
VERSION_FIELD = "Version"
LANG_FIELD = "Lang"
BUILD_FAMILY_FIELD = "Build_family"
WORKFLOW_ACTION_FIELD = "Workflow_action"
DOC_PHASE_FIELD = "Doc_phase"
GIT_REF_FIELD = "Git_ref"
BUILD_STARTED_AT_FIELD = "\u5f00\u59cb\u6784\u5efa\u65f6\u95f4"
DOCUMENT_DIRECTORY_FIELD = "Document directory"
DOCUMENT_LINK_FIELD = "Document link"
DOCUMENT_LINK_DD_FIELD = "Document link_dd"
UPLOAD_DINGTALK_FIELD = "是否上传钉钉"
DINGTALK_TARGET_NODE_URL_FIELD = "DingTalk_target_node_url"
DINGTALK_TARGET_NODE_URL_ALIASES = ("钉钉上传节点",)
OPERATOR_UNION_ID_FIELD = "operator_union_id"
DEFAULT_TARGET_NODE_URL_FIELD = "default_target_node_url"
IMMEDIATE_TRIGGER_FIELD = "\u662f\u5426\u7acb\u5373\u6784\u5efa"
FORCE_PHASE2_REFRESH_FIELD = "\u662f\u5426\u5f3a\u5236\u5237\u65b0\u6570\u636e"
DATA_SYNC_FIELD = "data_sync"

SUCCESS_PREFIX = "SUCCESS"
FAILED_PREFIX = "FAILED"
TRIGGER_VALUES = {"1", "true", "y", "yes"}
DONE_TRIGGER_VALUE = "\u5df2\u6784\u5efa"


@dataclass(frozen=True)
class DocumentLinkBinding:
    base_token_env: str
    table_id_env: str
    view_id_env: str | None
    wiki_parent_token_env: str | None
    base_token: str
    table_id: str
    view_id: str | None
    wiki_parent_token: str | None


@dataclass(frozen=True)
class QueueRecord:
    record_id: str
    document_id: str
    document_key: str
    version: str
    lang: str
    workflow_action: str = ""
    doc_phase: str = ""
    git_ref: str = ""
    trigger_value: str = ""
    immediate_trigger_value: Any = None
    force_phase2_refresh_value: Any = None
    upload_dingtalk_value: Any = None
    dingtalk_target_node_url: str = ""
    operator_union_id: str = ""
    default_target_node_url: str = ""
    build_family: str = ""

    @property
    def label(self) -> str:
        return self.document_id or f"{self.document_key}_{self.lang}"


@dataclass(frozen=True)
class WikiDestination:
    space_id: str
    parent_wiki_token: str
