import test from "node:test";
import assert from "node:assert/strict";

import { classifyTaskState, rowLooksFreshFailure, rowLooksFreshSuccess } from "../lib/status-classify.mjs";

test("a fresh successful Base row classifies as completed without needing the run", () => {
  const row = { result: "SUCCESS", result_is_fresh: true, freshness_status: "fresh_success" };
  assert.equal(rowLooksFreshSuccess(row), true);
  assert.equal(classifyTaskState({ row, runStatus: null }), "completed");
});

test("a fresh failed Base row classifies as failed", () => {
  const row = { result: "FAILED: missing spec", result_is_fresh: true, freshness_status: "fresh_failure" };
  assert.equal(rowLooksFreshFailure(row), true);
  assert.equal(classifyTaskState({ row, runStatus: null }), "failed");
});

test("a not-fresh row uses the live run state: running -> processing", () => {
  const row = { result: "", result_is_fresh: false, freshness_status: "writeback_pending" };
  assert.equal(classifyTaskState({ row, runStatus: { state: "processing", status: "in_progress" } }), "processing");
});

test("a not-fresh row with a failed run classifies as failed (failure before writeback)", () => {
  const row = { result: "", result_is_fresh: false, freshness_status: "writeback_pending" };
  assert.equal(classifyTaskState({ row, runStatus: { state: "failed", conclusion: "failure" } }), "failed");
  assert.equal(classifyTaskState({ row, runStatus: { state: "", conclusion: "timed_out" } }), "failed");
});

test("a run GitHub has finished but whose result is not written back is still processing", () => {
  const row = { result: "", result_is_fresh: false, freshness_status: "writeback_pending" };
  // run completed-success, but the deliverable is not in the table yet
  assert.equal(classifyTaskState({ row, runStatus: { state: "completed", status: "completed", conclusion: "success" } }), "processing");
});

test("with no run info and an unfresh row, default to processing (not failure)", () => {
  const row = { result: "", result_is_fresh: false, freshness_status: "writeback_pending" };
  assert.equal(classifyTaskState({ row, runStatus: null }), "processing");
});
