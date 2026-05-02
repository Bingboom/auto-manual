import fs from "node:fs/promises";
import path from "node:path";

function emptyState() {
  return {
    processedEvents: [],
    pendingPublishes: {},
    conversationContexts: {},
  };
}

async function ensureParent(filePath) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
}

async function readState(filePath) {
  try {
    const text = await fs.readFile(filePath, "utf8");
    const parsed = JSON.parse(text);
    return {
      processedEvents: Array.isArray(parsed?.processedEvents) ? parsed.processedEvents : [],
      pendingPublishes: parsed?.pendingPublishes && typeof parsed.pendingPublishes === "object" ? parsed.pendingPublishes : {},
      conversationContexts:
        parsed?.conversationContexts && typeof parsed.conversationContexts === "object" ? parsed.conversationContexts : {},
    };
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return emptyState();
    }
    throw error;
  }
}

async function writeState(filePath, state) {
  await ensureParent(filePath);
  const tmpPath = `${filePath}.tmp`;
  await fs.writeFile(tmpPath, `${JSON.stringify(state, null, 2)}\n`, "utf8");
  await fs.rename(tmpPath, filePath);
}

export function createStateStore(filePath, { now = () => Date.now(), maxProcessedEvents = 500 } = {}) {
  let stateWriteChain = Promise.resolve();

  function confirmationKey({ chatId, senderId }) {
    return `${chatId}:${senderId}`;
  }

  function contextKey({ chatId, senderId }) {
    return `${chatId}:${senderId}`;
  }

  async function withState(mutator) {
    const run = async () => {
      const state = await readState(filePath);
      const nextState = (await mutator(state)) || state;
      await writeState(filePath, nextState);
      return nextState;
    };
    const operation = stateWriteChain.then(run, run);
    stateWriteChain = operation.catch(() => {});
    return operation;
  }

  return {
    async claimProcessedEvent(eventId) {
      let claimed = false;
      await withState((state) => {
        const exists = state.processedEvents.some((entry) => entry?.id === eventId);
        if (exists) {
          return state;
        }
        const nextEvents = state.processedEvents.filter((entry) => entry?.id !== eventId);
        nextEvents.push({ id: eventId, processedAt: now() });
        state.processedEvents = nextEvents.slice(-maxProcessedEvents);
        claimed = true;
        return state;
      });
      return claimed;
    },
    async hasProcessedEvent(eventId) {
      const state = await readState(filePath);
      return state.processedEvents.some((entry) => entry?.id === eventId);
    },
    async markProcessedEvent(eventId) {
      await withState((state) => {
        const nextEvents = state.processedEvents.filter((entry) => entry?.id !== eventId);
        nextEvents.push({ id: eventId, processedAt: now() });
        state.processedEvents = nextEvents.slice(-maxProcessedEvents);
        return state;
      });
    },
    async rememberPendingPublish({ chatId, senderId, messageId, row, queryText, ttlSeconds }) {
      await withState((state) => {
        state.pendingPublishes[confirmationKey({ chatId, senderId })] = {
          chatId,
          senderId,
          messageId,
          row,
          queryText,
          createdAt: now(),
          expiresAt: now() + ttlSeconds * 1000,
        };
        return state;
      });
    },
    async consumePendingPublish({ chatId, senderId }) {
      let matched = null;
      await withState((state) => {
        const key = confirmationKey({ chatId, senderId });
        const pending = state.pendingPublishes[key];
        delete state.pendingPublishes[key];
        if (pending && pending.expiresAt > now()) {
          matched = pending;
        }
        for (const [candidateKey, candidate] of Object.entries(state.pendingPublishes)) {
          if (!candidate || candidate.expiresAt <= now()) {
            delete state.pendingPublishes[candidateKey];
          }
        }
        return state;
      });
      return matched;
    },
    async clearExpiredPublishes() {
      await withState((state) => {
        for (const [key, candidate] of Object.entries(state.pendingPublishes)) {
          if (!candidate || candidate.expiresAt <= now()) {
            delete state.pendingPublishes[key];
          }
        }
        return state;
      });
    },
    async rememberConversationContext({ chatId, senderId, messageId, row, queryText, actionName, ttlSeconds }) {
      if (!row || typeof row !== "object" || !row.record_id) {
        return;
      }
      await withState((state) => {
        state.conversationContexts[contextKey({ chatId, senderId })] = {
          chatId,
          senderId,
          messageId,
          row,
          queryText,
          actionName,
          createdAt: now(),
          expiresAt: now() + ttlSeconds * 1000,
        };
        return state;
      });
    },
    async readConversationContext({ chatId, senderId }) {
      let matched = null;
      await withState((state) => {
        const key = contextKey({ chatId, senderId });
        const context = state.conversationContexts[key];
        if (context && context.expiresAt > now()) {
          matched = context;
        } else if (context) {
          delete state.conversationContexts[key];
        }
        for (const [candidateKey, candidate] of Object.entries(state.conversationContexts)) {
          if (!candidate || candidate.expiresAt <= now()) {
            delete state.conversationContexts[candidateKey];
          }
        }
        return state;
      });
      return matched;
    },
    async clearExpiredConversationContexts() {
      await withState((state) => {
        for (const [key, candidate] of Object.entries(state.conversationContexts)) {
          if (!candidate || candidate.expiresAt <= now()) {
            delete state.conversationContexts[key];
          }
        }
        return state;
      });
    },
  };
}
