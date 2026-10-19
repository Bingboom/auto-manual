"""Feishu cloud-doc backport (CQ-1.3 pilot package).

Entry point: ``python -m tools.backport.cloud_doc <command>``; the historical
``python tools/backport/cloud_doc.py <command>`` stays available through a shim.
``cloud_doc`` is the re-export facade, ``cli`` owns ``main()``, and the other
modules are the split leaves (args, commands, orchestration, model, apply,
reports, render, routing, pr, transports, util).
"""
