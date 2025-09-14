import sys
import types
import importlib.util
import pathlib
import pytest

PACKAGE_NAME = "custom_components.imou_control"
PACKAGE_PATH = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "imou_control"


def _ensure_package() -> types.ModuleType:
    if "custom_components" not in sys.modules:
        sys.modules["custom_components"] = types.ModuleType("custom_components")
    pkg = sys.modules.get(PACKAGE_NAME)
    if pkg is None:
        pkg = types.ModuleType(PACKAGE_NAME)
        pkg.__path__ = [str(PACKAGE_PATH)]
        sys.modules[PACKAGE_NAME] = pkg
        # load const to expose endpoints
        spec_const = importlib.util.spec_from_file_location(
            f"{PACKAGE_NAME}.const", PACKAGE_PATH / "const.py"
        )
        mod_const = importlib.util.module_from_spec(spec_const)
        sys.modules[f"{PACKAGE_NAME}.const"] = mod_const
        spec_const.loader.exec_module(mod_const)
        pkg.TOKEN_ENDPOINT = mod_const.TOKEN_ENDPOINT
        pkg.PTZ_LOCATION_ENDPOINT = mod_const.PTZ_LOCATION_ENDPOINT
        # load utils helper
        spec_utils = importlib.util.spec_from_file_location(
            f"{PACKAGE_NAME}.utils", PACKAGE_PATH / "utils.py"
        )
        mod_utils = importlib.util.module_from_spec(spec_utils)
        sys.modules[f"{PACKAGE_NAME}.utils"] = mod_utils
        spec_utils.loader.exec_module(mod_utils)
    return pkg


def import_imou_module(name: str):
    _ensure_package()
    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE_NAME}.{name}", PACKAGE_PATH / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{PACKAGE_NAME}.{name}"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def token_module():
    return import_imou_module("token_manager")


@pytest.fixture
def api_module():
    return import_imou_module("api")
