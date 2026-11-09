"""Opt-in, context-bound manual Q&A entrance; no credentials in static pages."""
from __future__ import annotations

from html import escape
from urllib.parse import urlsplit

from tools.rtd.feedback import normalize_channels


def chat_endpoint(raw: str) -> str:
    if not raw:
        return ""
    url = urlsplit(raw)
    if (any(ord(char) < 33 for char in raw) or url.scheme != "https" or not url.hostname or url.username or url.password
            or url.query or url.fragment or url.path not in ("", "/")):
        raise ValueError("HT_DOCS_CHAT_URL must be an HTTPS origin without credentials or a path")
    normalize_channels([{"label": "Manual Q&A", "url": raw}])
    return raw.rstrip("/")


def manual_chat_markup(endpoint: str, publication: dict) -> str:
    """Use frozen publication metadata, never infer locale/version from a filename."""
    if not endpoint:
        return ""
    endpoint = chat_endpoint(endpoint)
    attrs = {"endpoint": endpoint, "model": publication["model"], "region": publication["region"],
             "language": publication.get("lang") or "", "version": publication.get("version") or "",
             "page": publication["url"]}
    data = " ".join(f'data-{key}="{escape(value, quote=True)}"' for key, value in attrs.items())
    label = " · ".join(attrs[key] or "未确认" for key in ("model", "region", "language", "version"))
    return (
        f'<aside class="manual-chat" lang="zh-CN" dir="ltr" {data}>'
        '<button class="manual-chat-launch" type="button" aria-haspopup="dialog" '
        'aria-controls="manual-chat-dialog" hidden>问 HT-Docs bot</button>'
        '<dialog id="manual-chat-dialog" aria-labelledby="manual-chat-title">'
        '<header class="manual-chat-header"><div><p class="manual-chat-eyebrow">产品资料查询助手</p>'
        '<h2 id="manual-chat-title">HT-Docs bot</h2></div>'
        '<button class="manual-chat-close" type="button" aria-label="关闭对话">×</button></header>'
        f'<p class="manual-chat-context">{escape(label)}</p>'
        '<div class="manual-chat-messages" role="log" aria-label="对话记录" aria-live="polite">'
        '<p class="manual-chat-bot">你好，可以向我询问这份说明书中的规格、操作方法或故障处理。'
        '回答会附原文出处，资料不足时会明确说明。</p></div>'
        '<p class="manual-chat-status" role="status"></p>'
        '<form class="manual-chat-login"><label>问答访问密码'
        '<input name="password" type="password" autocomplete="current-password" required maxlength="256">'
        '</label><button type="submit">开始对话</button></form>'
        '<form class="manual-chat-question" hidden><label class="manual-chat-sr" for="manual-chat-input">你的问题</label>'
        '<textarea id="manual-chat-input" name="question" rows="3" maxlength="1000" required '
        'placeholder="例如：如何进行太阳能充电？"></textarea>'
        '<div class="manual-chat-actions"><button class="manual-chat-clear" type="button">清空对话</button>'
        '<button type="submit">发送问题</button></div></form>'
        '<footer class="manual-chat-footer">问题将发送至本站配置的问答服务。请勿填写个人或订单信息。'
        '操作前请核对原文中的条件和安全警示。</footer></dialog></aside>'
    )


def page_chat(app, publication: dict) -> str:
    endpoint = chat_endpoint(getattr(app.config, "rtd_manual_chat_url", ""))
    if not endpoint:
        return ""
    app.add_js_file("manual-chat.js", loading_method="defer")
    app.add_css_file("manual-chat.css")
    return manual_chat_markup(endpoint, publication)
