import importlib.util as _importlib_util
import sysconfig as _sysconfig
import os as _os
import sys as _sys


def _patch_stdlib_platform() -> None:
    _current = _sys.modules[__name__]
    for _base in (_sysconfig.get_path("stdlib"), _sysconfig.get_path("platstdlib")):
        if not _base:
            continue
        _f = _os.path.join(_base, "platform.py")
        if _os.path.isfile(_f):
            _spec = _importlib_util.spec_from_file_location("_stdlib_platform", _f)
            _mod = _importlib_util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            for _attr in dir(_mod):
                if not _attr.startswith("_") and not hasattr(_current, _attr):
                    setattr(_current, _attr, getattr(_mod, _attr))
            return


_patch_stdlib_platform()
del _patch_stdlib_platform
