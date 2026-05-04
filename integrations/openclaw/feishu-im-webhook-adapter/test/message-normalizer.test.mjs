import test from "node:test";
import assert from "node:assert/strict";

import { normalizeIncomingMessage } from "../lib/message-normalizer.mjs";

test("normalizeIncomingMessage applies local aliases before resolution", () => {
  const normalized = normalizeIncomingMessage({
    messageText: "查 private target 草稿包",
    localProfile: {
      aliases: [{ from: "private target", to: "JE-1000F US", caseSensitive: false, match: "literal" }],
    },
  });

  assert.equal(normalized.normalizedText, "查 JE-1000F US 草稿包");
  assert.equal(normalized.usedLocalAliases, true);
  assert.equal(normalized.usedConversationContext, false);
});

test("normalizeIncomingMessage appends previous record id for pronoun follow-ups", () => {
  const normalized = normalizeIncomingMessage({
    messageText: "这个好了没",
    conversationContext: {
      row: {
        record_id: "rec_context",
      },
    },
  });

  assert.equal(normalized.normalizedText, "这个好了没 record_id rec_context");
  assert.equal(normalized.usedConversationContext, true);
  assert.equal(normalized.contextRecordId, "rec_context");
});

test("normalizeIncomingMessage does not use context when the message has an explicit target", () => {
  const normalized = normalizeIncomingMessage({
    messageText: "这个 JE-1000F_US_0.3 好了没",
    conversationContext: {
      row: {
        record_id: "rec_context",
      },
    },
  });

  assert.equal(normalized.normalizedText, "这个 JE-1000F_US_0.3 好了没");
  assert.equal(normalized.usedConversationContext, false);
});

test("normalizeIncomingMessage treats task ids as explicit targets", () => {
  const normalized = normalizeIncomingMessage({
    messageText: "这个 JE-1000F_US_1.0_Build Draft Package 好了没",
    conversationContext: {
      row: {
        record_id: "rec_context",
      },
    },
  });

  assert.equal(normalized.normalizedText, "这个 JE-1000F_US_1.0_Build Draft Package 好了没");
  assert.equal(normalized.usedConversationContext, false);
});

test("normalizeIncomingMessage treats model plus chinese market alias as an explicit target", () => {
  const normalized = normalizeIncomingMessage({
    messageText: "构建JE-1000F的所有欧规说明书文案",
    conversationContext: {
      row: {
        record_id: "rec_context",
      },
    },
  });

  assert.equal(normalized.normalizedText, "构建JE-1000F的所有欧规说明书文案");
  assert.equal(normalized.usedConversationContext, false);
});

test("normalizeIncomingMessage does not append previous record ids to execution requests", () => {
  const normalized = normalizeIncomingMessage({
    messageText: "重新构建这个",
    conversationContext: {
      row: {
        record_id: "rec_context",
      },
    },
  });

  assert.equal(normalized.normalizedText, "重新构建这个");
  assert.equal(normalized.usedConversationContext, false);
});
