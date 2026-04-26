---
name: feishu-auto-get
description: "Immediately add a Feishu Get reaction to inbound DM messages."
metadata:
  {
    "openclaw": {
      "emoji": "🫡",
      "events": ["message:received"],
      "requires": { "bins": ["openclaw"] }
    }
  }
---

# Feishu Auto Get

Adds a native Feishu `Get` reaction as soon as an inbound Feishu DM message is
received.

This hook is intended for operator-facing acknowledgement, so the user gets an
instant native reaction before the main agent decides whether it also needs to
send a text reply.
