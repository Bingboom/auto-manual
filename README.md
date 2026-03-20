# Auto-Manual Tool

Updated: 2026-03-17

Auto-Manual is the repository that turns structured content into target-specific manual bundles and release outputs.
It owns the current build, review, validation, revision tracking, and publish flow for this repo.

## 1. Current Role

This repository is responsible for:

- generating target-specific runtime bundles from templates and phase1 CSV data
- moving target-specific editing into [`docs/_review/`](docs/_review) once review starts
- validating review/runtime bundles before release
- exporting revision reports and release manifests

This repository is not the place to define the long-term platform strategy.
That boundary lives in [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md).

## 2. Primary Entrypoint

The primary entrypoint is [`build.py`](build.py).

Typical review-first flow:

```bash
python3 build.py doctor --config config.yaml --model JE-1000F --region US
python3 build.py rst --config config.yaml --model JE-1000F --region US --source runtime
python3 build.py review --config config.yaml --model JE-1000F --region US
python3 build.py check --config config.yaml --model JE-1000F --region US
python3 build.py publish --config config.yaml --model JE-1000F --region US
```

Do not treat this file as the full command reference.
The command semantics and output layout are maintained in [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md).

## 3. Editing Surfaces

Use different surfaces for different stages:

- shared template changes: [`docs/templates/`](docs/templates)
- structured data changes: [`data/phase1/`](data/phase1)
- target-specific review edits after review starts: [`docs/_review/`](docs/_review)
- generated runtime and export outputs: [`docs/_build/`](docs/_build)

Rule:

- before review starts, seed the draft from templates and data
- after review starts, edit `_review`
- do not use `_build` as the long-lived editing surface

The current user workflow and source-of-truth rules are maintained in [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md).

## 4. Document Map

Use the document that owns the topic:

- current maintainer command reference: [`code-as-doc/build_doc_guide.md`](code-as-doc/build_doc_guide.md)
- current user workflow and editing rules: [`user-guide/hello_auto-doc.md`](user-guide/hello_auto-doc.md)
- happy-path example: [`user-guide/quick_start_guide.md`](user-guide/quick_start_guide.md)
- maintainer doc index: [`code-as-doc/README.md`](code-as-doc/README.md)
- current repository component map: [`code-as-doc/architecture/Hello_Docs_Architecture.md`](code-as-doc/architecture/Hello_Docs_Architecture.md)
- future canonical content model: [`code-as-doc/architecture/Content_Data_Model.md`](code-as-doc/architecture/Content_Data_Model.md)
- long-term strategy and stable architecture boundaries: [`code-as-doc/architecture/System Evolution Strategy.md`](code-as-doc/architecture/System%20Evolution%20Strategy.md)
- repo-level execution roadmap: [`optimization_project.md`](optimization_project.md)

## 5. Key Directories

- [`build.py`](build.py): top-level CLI entrypoint
- [`tools/`](tools): orchestration, rendering, validation, diff, and release helpers
- [`data/phase1/`](data/phase1): current operational CSV snapshot inputs
- [`docs/templates/`](docs/templates): shared seed templates
- [`docs/_review/`](docs/_review): target-specific review layer
- [`docs/_build/`](docs/_build): runtime bundles and export outputs
- [`reports/`](reports): revision reports and release manifests
- [`tests/`](tests): automated regression coverage

## 6. Maintenance Rule

When command behavior, workflow ownership, or architecture boundaries change:

- update the owning document in the same change
- avoid restating the same rules in multiple docs
- keep history in [`code-as-doc/code_optimization_log.md`](code-as-doc/code_optimization_log.md), not in the current guides
