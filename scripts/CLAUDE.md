# Scripts Directory

`scripts/` contains repository helper scripts for branch creation, local builds, queue services, and environment checks.

## Map

- `start_branch.sh` and `start_branch.ps1`: required branch wrappers for new work.
- `git_branch_guard.py` and `openclaw_git_guard.py`: branch and push safety.
- `local_build.*` and `build_us_jp_manuals.*`: local build helpers.
- `process_build_queue*.ps1`, `listen_build_queue.ps1`: queue service wrappers.
- `run_feishu_im_*`: service launch helpers.

## Local Rules

- Keep shell, PowerShell, and Python variants behaviorally aligned when they are paired.
- Do not weaken branch or push safety without explicit operator confirmation.
- Prefer non-interactive commands and deterministic exits; these scripts are used by agents and hooks.

## Validation

- Script-related tests: `python3 -m unittest tests.test_git_branch_guard tests.test_openclaw_git_guard tests.test_local_build tests.test_build_us_jp_manuals`
- Lint Python scripts: `python3 -m ruff check scripts`
- Branch wrapper smoke test only on a clean tree: `bash scripts/start_branch.sh <type>/<area>-<topic>`
