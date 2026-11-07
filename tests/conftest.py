"""Load the integration's HA-free modules (const, api) without importing Home Assistant."""
import sys
import types
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "ski_conditions"
pkg = types.ModuleType("ski_conditions")
pkg.__path__ = [str(PKG_DIR)]
sys.modules.setdefault("ski_conditions", pkg)
