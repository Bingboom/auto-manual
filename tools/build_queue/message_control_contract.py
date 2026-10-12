from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ACTION_QUERY_STATUS = "query_status"
ACTION_START_REVIEW = "start_review"
ACTION_BUILD_DRAFT_PACKAGE = "build_draft_package"
ACTION_PUBLISH = "publish"

STATUS_READY = "ready"
STATUS_NEEDS_INPUT = "needs_input"
STATUS_NEEDS_CONFIRMATION = "needs_confirmation"
STATUS_UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class MessageTargetSelector:
    record_id: str = ""
    document_id: str = ""
    document_key: str = ""
    model: str = ""
    region: str = ""
    lang: str = ""
    build_family: str = ""
    git_ref: str = ""
    version: str = ""

    def to_dict(self) -> dict[str, str]:
        data: dict[str, str] = {}
        for key, value in (
            ("record_id", self.record_id),
            ("document_id", self.document_id),
            ("document_key", self.document_key),
            ("model", self.model),
            ("region", self.region),
            ("lang", self.lang),
            ("build_family", self.build_family),
            ("git_ref", self.git_ref),
            ("version", self.version),
        ):
            if value:
                data[key] = value
        return data


@dataclass(frozen=True)
class MessageControlRoute:
    state_surface: str
    workflow_action: str = ""
    workflow_file: str = ""
    reply_fields: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"state_surface": self.state_surface}
        if self.workflow_action:
            data["workflow_action"] = self.workflow_action
        if self.workflow_file:
            data["workflow_file"] = self.workflow_file
        if self.reply_fields:
            data["reply_fields"] = list(self.reply_fields)
        return data


@dataclass(frozen=True)
class MessageControlResolution:
    phase: str
    raw_message: str
    normalized_message: str
    action: str = ""
    status: str = STATUS_UNRESOLVED
    selector: MessageTargetSelector = MessageTargetSelector()
    missing_fields: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    confirmation_required: bool = False
    confirmed: bool = False
    route: MessageControlRoute | None = None
    resolved_config_path: str = ""
    known_build_families: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "phase": self.phase,
            "raw_message": self.raw_message,
            "normalized_message": self.normalized_message,
            "status": self.status,
            "selector": self.selector.to_dict(),
        }
        if self.action:
            data["action"] = self.action
        if self.missing_fields:
            data["missing_fields"] = list(self.missing_fields)
        if self.warnings:
            data["warnings"] = list(self.warnings)
        if self.confirmation_required:
            data["confirmation_required"] = True
        if self.confirmed:
            data["confirmed"] = True
        if self.route is not None:
            data["route"] = self.route.to_dict()
        if self.resolved_config_path:
            data["resolved_config_path"] = self.resolved_config_path
        if self.known_build_families:
            data["known_build_families"] = list(self.known_build_families)
        return data
