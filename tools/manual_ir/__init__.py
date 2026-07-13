"""Renderer-neutral semantic manual intermediate representation."""

from .builder import build_manual_ir
from .model import ManualBlock, ManualIR, ManualPage
from .serialize import read_manual_ir, write_manual_ir
from .validate import validate_manual_ir

__all__ = [
    "ManualBlock",
    "ManualIR",
    "ManualPage",
    "build_manual_ir",
    "read_manual_ir",
    "validate_manual_ir",
    "write_manual_ir",
]
