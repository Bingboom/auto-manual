# PR Title

[Feature/Fix/Refactor] short summary

---

## Summary

- What changed:
- Why it changed:

---

## Change Type

- [ ] Feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Performance
- [ ] Config / schema change
- [ ] Workflow / CI change

---

## Impact Surface

- [ ] CSV schema / structured snapshot
- [ ] Template / page assembly
- [ ] Build entrypoint / CLI
- [ ] Review / diff / publish / release flow
- [ ] External integrations (Feishu / DingTalk / OpenClaw)
- [ ] Docs / CI / maintainer workflow

---

## Anti-Debt Checklist

- [ ] New low-level logic was kept out of `build.py`, `tools/build_docs.py`, and `tools/process_build_queue.py`
- [ ] If helper boundaries changed, `code-as-doc/dev/orchestration_module_map.md` was updated in the same PR
- [ ] If behavior or workflow semantics changed, `README.md`, `code-as-doc/build_doc_guide.md`, and `user-guide/hello_auto-doc.md` were updated in the same PR
- [ ] `python tools/check_maintainability_guardrails.py` passes locally
- [ ] No new config was added only because the model changed

---

## Validation

- [ ] `python -m unittest`
- [ ] `python build.py check --config ... --model ... --region ...`
- [ ] Additional targeted verification:
