from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Phase0SpikeItem:
    key: str
    title: str
    success_criteria: str


PHASE0_SPIKE_ITEMS: tuple[Phase0SpikeItem, ...] = (
    Phase0SpikeItem(
        key="auth",
        title="Acquire App-Only token",
        success_criteria="Worker can obtain and refresh an app token without manual intervention.",
    ),
    Phase0SpikeItem(
        key="records_list",
        title="List candidate queue rows",
        success_criteria="Structured-data product returns rows with a stable record identifier.",
    ),
    Phase0SpikeItem(
        key="record_update",
        title="Write a harmless field update",
        success_criteria="One row can be updated and re-read without replacing the entire dataset.",
    ),
    Phase0SpikeItem(
        key="file_upload",
        title="Upload sample docx",
        success_criteria="A local .docx can be uploaded and returns a reusable file identifier.",
    ),
    Phase0SpikeItem(
        key="share_url",
        title="Resolve tenant-visible file URL",
        success_criteria="Uploaded file resolves to a link suitable for Document_link writeback.",
    ),
    Phase0SpikeItem(
        key="workspace_attach",
        title="Check attach-to-workspace support",
        success_criteria="We get a clear yes/no answer on container attach support and permissions.",
    ),
)


def phase0_checklist() -> tuple[Phase0SpikeItem, ...]:
    return PHASE0_SPIKE_ITEMS
