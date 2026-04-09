from __future__ import annotations

from .contracts import DingTalkAccessToken


def get_app_only_token(*, client_id_env: str, client_secret_env: str, corp_id_env: str | None = None) -> DingTalkAccessToken:
    raise NotImplementedError(
        "Phase 0 placeholder: implement DingTalk App-Only token acquisition after the product and auth flow are verified."
    )
