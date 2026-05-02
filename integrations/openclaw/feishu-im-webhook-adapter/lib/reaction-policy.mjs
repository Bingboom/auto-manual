import { localReactionEmojiType } from "./local-profile.mjs";

const DEFAULT_STAGE_REACTIONS = {
  received: "SMILE",
  accepted: "OK",
  completed: "OK",
  needs_confirmation: "SMILE",
  needs_input: "SMILE",
  unresolved: "SMILE",
  error: "SMILE",
};

export function reactionEmojiForStage(stage, localProfile = null) {
  return localReactionEmojiType(localProfile, stage) || DEFAULT_STAGE_REACTIONS[stage] || "";
}

export async function sendStageReaction({ config, feishuClient, localProfile, logger = console, messageId, stage }) {
  if (!config?.enableMessageReactions || !messageId || typeof feishuClient?.addMessageReaction !== "function") {
    return false;
  }
  const emojiType = reactionEmojiForStage(stage, localProfile);
  if (!emojiType) {
    return false;
  }
  try {
    await feishuClient.addMessageReaction(messageId, emojiType);
    return true;
  } catch (error) {
    logger.warn?.(`[feishu-im-webhook-adapter] message reaction failed (${stage}/${emojiType})`, error);
    return false;
  }
}
