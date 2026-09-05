"""Renderer-neutral semantic manual intermediate representation."""

from .builder import build_manual_ir, build_manual_ir_from_source
from .model import ManualBlock, ManualIR, ManualPage
from .source import ManualSource, SourcePage
from .serialize import read_manual_ir, write_manual_ir
from .validate import ManualIRValidationError, unknown_language_issues, validate_manual_ir

__all__ = [
    "ManualBlock",
    "ManualIR",
    "ManualIRValidationError",
    "ManualPage",
    "ManualSource",
    "SourcePage",
    "build_manual_ir",
    "build_manual_ir_from_source",
    "read_manual_ir",
    "unknown_language_issues",
    "validate_manual_ir",
    "write_manual_ir",
]
