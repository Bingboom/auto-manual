"""Read-only corpus harvesters for staging Translation_Memory candidates."""

from tools.corpus.harvest_web_ir import HARVEST_SCHEMA_VERSION, harvest_web_ir

__all__ = ["HARVEST_SCHEMA_VERSION", "harvest_web_ir"]
