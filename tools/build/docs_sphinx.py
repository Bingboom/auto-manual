from __future__ import annotations

from typing import Callable


def build_rst_epilog(substitutions: dict[str, str]) -> str:
    lines: list[str] = []
    for key, value in substitutions.items():
        text = (value or "").strip()
        if not text:
            continue
        lines.append(f".. |{key}| replace:: {text}")
    return "\n".join(lines)


def with_rst_epilog(
    cmd: list[str],
    substitutions: dict[str, str] | None,
    *,
    build_rst_epilog: Callable[[dict[str, str]], str],
) -> list[str]:
    if not substitutions:
        return cmd
    epilog = build_rst_epilog(substitutions)
    if not epilog:
        return cmd
    return [*cmd, "-D", f"rst_epilog={epilog}"]


def with_product_name_epilog(
    cmd: list[str],
    product_name: str | None,
    *,
    with_rst_epilog: Callable[[list[str], dict[str, str] | None], list[str]],
) -> list[str]:
    if not (product_name or "").strip():
        return cmd
    name = product_name.strip()
    return with_rst_epilog(
        cmd,
        {
            "PRODUCT_NAME": name,
            "PRODUCT_NAME_BOLD": f"**{name}**",
        },
    )


def resolve_sphinx_build_cmd(
    builder: str,
    *,
    find_exe: Callable[[list[str]], str | None],
    python_executable: str,
) -> list[str]:
    sphinx_build = find_exe(["sphinx-build"])
    if sphinx_build:
        return [sphinx_build, "-b", builder]
    return [python_executable, "-m", "sphinx", "-b", builder]
