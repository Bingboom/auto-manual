import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

async function readState(stateFile) {
  try {
    const raw = await readFile(stateFile, "utf8");
    const parsed = JSON.parse(raw);
    return {
      lastRecord: parsed?.lastRecord || null,
      recordsByRunId: parsed?.recordsByRunId || {},
      recordsByWorkflowFile: parsed?.recordsByWorkflowFile || {},
    };
  } catch (error) {
    return {
      lastRecord: null,
      recordsByRunId: {},
      recordsByWorkflowFile: {},
    };
  }
}

async function writeState(stateFile, state) {
  await mkdir(dirname(stateFile), { recursive: true });
  await writeFile(stateFile, JSON.stringify(state, null, 2) + "\n", "utf8");
}

export function createStateStore(stateFile) {
  return {
    async getLastRecord() {
      const state = await readState(stateFile);
      return state.lastRecord || null;
    },
    async getRecordByRunId(runId) {
      const state = await readState(stateFile);
      return state.recordsByRunId?.[String(runId)] || null;
    },
    async getLastRecordForWorkflow(workflowFile) {
      const state = await readState(stateFile);
      return state.recordsByWorkflowFile?.[String(workflowFile)] || null;
    },
    async saveRecord(record) {
      const state = await readState(stateFile);
      state.lastRecord = record;
      if (record.runId) {
        state.recordsByRunId[String(record.runId)] = record;
      }
      if (record.workflowFile) {
        state.recordsByWorkflowFile[String(record.workflowFile)] = record;
      }
      await writeState(stateFile, state);
      return record;
    },
  };
}
