# Recipes

Concrete patterns for the practices in `SKILL.md`. Copy and adapt; the point is the shape, not the exact code.

## Table of contents

- [Golden byte-comparison scaffold](#golden-byte-comparison-scaffold)
- [Anchored line-surgery for verbatim moves](#anchored-line-surgery-for-verbatim-moves)
- [Scripted word-boundary rename](#scripted-word-boundary-rename)
- [Façade + delegate decomposition](#façade--delegate-decomposition)
- [Registry parity test](#registry-parity-test)
- [Discovery + plan report shape](#discovery--plan-report-shape)

---

## Golden byte-comparison scaffold

Pins the *real* output of a pipeline so any behavior change fails loudly. Build the artifact through the real entrypoint (a subprocess CLI call is closest to reality), then compare every part against a committed snapshot, normalizing only the non-deterministic bits.

```python
def _normalized_parts(path):
    # Compare every part of a composite artifact (here: a zip/.idml).
    # Normalize the ONE thing that legitimately varies between machines —
    # the absolute repo path baked into file:// URIs — to a fixed token,
    # so a real refactor stays green but a real output change does not.
    parts = {}
    with zipfile.ZipFile(path) as zf:
        for name in sorted(zf.namelist()):
            data = zf.read(name).decode("utf-8", "surrogatepass")
            data = data.replace(ROOT.resolve().as_uri(), "file://GOLDEN-ROOT")
            parts[name] = data
    return parts

def test_matches_golden(self):
    built = _normalized_parts(_build_via_cli(...))   # real entrypoint
    for name, golden in _load_golden().items():
        self.assertEqual(built[name], golden, f"{name} drifted")
    self.assertEqual(set(built), set(_load_golden()))  # no extra/missing parts

# A --regenerate entry point exists, but running it is a DELIBERATE, REVIEWED
# act: read the resulting diff and confirm its scope is exactly intended.
```

Rules that make it trustworthy:
- Build through the same entrypoint users hit, not an internal shortcut.
- Normalize the *minimum* — over-normalizing hides real regressions.
- A diff during a "pure refactor" means the refactor was not pure. Investigate before rebaselining.

## Anchored line-surgery for verbatim moves

When extracting a block of lines to move it elsewhere unchanged, assert the boundaries first so the script aborts (instead of grabbing the wrong range) if the file shifted under you.

```python
lines = src.read_text().splitlines(keepends=True)

# Anchors: the exact text expected at the cut boundaries. If either fails,
# the file moved and blindly slicing [start:end] would corrupt the move.
assert lines[START].strip() == "def build_story(writer, block):", lines[START]
assert lines[END].strip() == "return out", lines[END]

moved = lines[START:END + 1]
```

If an anchor assertion fires, re-locate the true boundary and fix the index — never widen the slice to "make it work".

## Scripted word-boundary rename

Renaming an identifier during a move (e.g. detaching a method from `self`) must not touch look-alikes.

```python
# Correct: only the whole word `self`, not `self_id` or `myself`.
body = re.sub(r"\bself\b", "writer", body)
```

Prefer a scripted rename over hand-editing: it is auditable (you see the regex), repeatable (rerun after a rebase), and it will not silently miss the one occurrence in an `else` branch you did not scroll to.

## Façade + delegate decomposition

Split a monolith without moving anything the outside world can see.

1. Create the new modules; move the implementation there verbatim (via anchored surgery).
2. In the original file, re-export every public name: `from .newmod import build_story, ...`.
3. Turn former methods into one-line delegates: `def build_story(self, b): return newmod.build_story(self, b)`.
4. Callers and existing tests import the same names and pass — proof the split changed nothing.

Lock it with tests:
- **Re-export surface**: assert every name in `FACADE_NAMES` is importable from the façade.
- **No reverse imports**: grep the new package for `import <facade_module>` — the dependency arrow must point one way only.
- **Delegate equality**: the façade method and the module function produce identical output for the same input.

## Registry parity test

When "add a feature" should mean "add one module + one registry entry", enforce that the two sides never drift.

```python
def test_every_emitted_kind_has_a_renderer(self):
    # The producer lists what it emits; the registry maps kind -> renderer.
    # If someone adds an emitted kind but forgets the renderer (or vice
    # versa), this fails — so "add a component" stays a one-module change.
    self.assertLessEqual(set(EMITTED_COMPONENT_KINDS), set(REGISTRY))
```

## Discovery + plan report shape

For a large task, write these two before any code and let the user confirm the plan.

`discovery_report.md`:
- **What exists**: the current structure, entrypoints, sizes.
- **Contracts**: what must not change (formats, CLI, exported names) and *why* — cite the file/line.
- **Traps**: the non-obvious landmines (a string that dodges a bug, a test that regenerates itself, a path that only breaks in one code path).

`implementation_plan.md`:
- **Ordered phases**, each independently shippable and revertable, with the one-line goal of each.
- **Per phase**: files touched, the safety net that pins it, the verification rungs to run.
- **Non-goals**: what this work deliberately does *not* do, so scope stays bounded.
