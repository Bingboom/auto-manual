"""IDML exporter internals (componentization of tools/export_idml.py).

Layering (imports point downward only; tools/export_idml.py is the façade
and CLI, and re-exports the public surface for existing callers/tests):

    params      shared constants + layout-parameter access
    loaders     phase2 CSV -> plain rows/dicts (incl. symbol copy l10n)
    primitives  XML building blocks (paragraph ranges, cells, tables, frames)
    styles      resource parts (styles / colors / fonts / preferences)
    check       structural .idml validation

Plan: reports/idml_componentization/20260705-01 (P1).
"""
