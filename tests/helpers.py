from __future__ import annotations

import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_NAME = "custom_components"
COMPONENT_NAME = "imou_control"
PACKAGE_PATH = ROOT / PACKAGE_NAME / COMPONENT_NAME


def _ensure_namespace_package() -> None:
    if PACKAGE_NAME not in sys.modules:
        namespace = types.ModuleType(PACKAGE_NAME)
        namespace.__path__ = [str(ROOT / PACKAGE_NAME)]  # type: ignore[attr-defined]
        sys.modules[PACKAGE_NAME] = namespace

    full_package = f"{PACKAGE_NAME}.{COMPONENT_NAME}"
    if full_package not in sys.modules:
        package = types.ModuleType(full_package)
        package.__path__ = [str(PACKAGE_PATH)]  # type: ignore[attr-defined]
        sys.modules[full_package] = package


def _ensure_usage_stub() -> None:
    usage_name = f"{PACKAGE_NAME}.{COMPONENT_NAME}.usage"
    if usage_name in sys.modules:
        return

    module = types.ModuleType(usage_name)

    class ApiUsageTracker:  # pragma: no cover - simple stub
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def note_call(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        async def async_load(self) -> None:
            return None

    module.ApiUsageTracker = ApiUsageTracker  # type: ignore[attr-defined]
    sys.modules[usage_name] = module


def load_imou_module(module: str):
    _ensure_namespace_package()
    _ensure_usage_stub()
    full_name = f"{PACKAGE_NAME}.{COMPONENT_NAME}.{module}"
    module_path = PACKAGE_PATH / f"{module}.py"
    spec = spec_from_file_location(full_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {full_name} from {module_path}")
    loaded = module_from_spec(spec)
    sys.modules[full_name] = loaded
    spec.loader.exec_module(loaded)
    return loaded
