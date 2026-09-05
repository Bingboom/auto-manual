"""Renderer-neutral semantic manual intermediate representation."""

from .builder import build_manual_ir
from .model import ManualBlock, ManualIR, ManualPage
from .serialize import read_manual_ir, write_manual_ir
from .validate import ManualIRValidationError, unknown_language_issues, validate_manual_ir

__all__ = [
    "ManualBlock",
    "ManualIR",
    "ManualIRValidationError",
    "ManualPage",
    "build_manual_ir",
    "read_manual_ir",
    "unknown_language_issues",
    "validate_manual_ir",
    "write_manual_ir",
]
