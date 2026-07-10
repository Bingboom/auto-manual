# Recipes

Use these patterns with `hardcore-task-execution`; adapt the details to the repository contract.

## Golden comparison

Build through the real CLI, normalize only genuinely machine-specific values, compare every artifact part, and fail on missing or extra parts. A diff during a pure refactor is a regression investigation, not an automatic baseline update.

## Anchored surgery

Before moving a block, assert the exact first and last source lines. If an anchor fails, re-locate the block instead of widening the slice.

```python
lines = source.read_text().splitlines(keepends=True)
assert lines[start].strip() == "def build_story(writer, block):"
assert lines[end].strip() == "return out"
moved = lines[start : end + 1]
```

## Word-boundary rename

Use `re.sub(r"\bself\b", "writer", body)` so look-alike identifiers remain untouched. Scripted edits are repeatable and auditable.

## Façade/delegate split

Move implementation verbatim, re-export the public names from the original module, and keep former methods as one-line delegates. Test re-exports, one-way imports, and delegate equality.

## Registry parity

When a producer emits kinds and a registry maps them to handlers, assert that every emitted kind is registered. This prevents feature additions from silently creating an unhandled branch.

## Discovery and plan reports

The discovery report records current structure, contracts, sizes, and traps with file references. The implementation plan records ordered, independently verifiable phases, touched files, safety nets, and non-goals.
