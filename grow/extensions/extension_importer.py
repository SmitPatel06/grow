"""Loads extensions, with a workaround for the frozen version."""

# NOTE: Here be dragons, specifically for the packaged application. There are
# no dragons present here when Grow runs in the normal environment. The very
# concept of importing and running external "plugin-like" code is antithetical
# to PyInstaller, whose goal is to package everything necessary for running a
# program into a single executable. However, we need to support the extension
# system in Grow, allowing users to write and run arbitrary Python code (which
# may or may not depend on other, external libraries).
#
# We attempted to include the entire stdlib in with the packaged app
# (https://github.com/grow/grow/commit/b4530658), though that wasn't
# sufficient. The Python stdlib os.py module has its own platform-specific
# magic that is performed upon execution, which was bizarrely incompatible with
# PyInstaller's module importers (on sys.meta_path). Other users of
# PyInstaller, attempting to implement something similar, encountered similar
# errors (https://stackoverflow.com/q/35254139).
#
# Other bizarre errors, beyond os.py, related to the stdlib would occur.
# Specifically, modules had difficulty importing the `exceptions` module. None
# of these errors would occur if these libraries simply relied on the system's
# `site-packages` and system Python library. To permit extensions to rely on
# the system `site-packages`, we can import Python's `site` module, which
# configures `sys.path` depending on the system.  Normally that would be
# enough, but PyInstaller overwrites the system `site` module with a `site`
# module that specifically prevents this behavior
# (https://github.com/pyinstaller/pyinstaller/issues/510).
#
# So, in order to leverage the default `site.py` `sys.path` configuration, we
# overwite PyInstaller's `site` module with our vendored copy of the default
# `site` module from Python (which we're calling `patched_site.py`. This was
# not enough, though, and we had to make one modification to
# `patched_site.py`'s main: preventing a magic function (`abs__file__()`) from
# being executed since its behavior was also not compatible with PyInstaller.
#
# After all is said and done, we reset `sys.path` after the extension is
# loaded, to prevent any permanent changes during runtime. There may be a more
# intelligent way to fix this situation by writing a custom module loader and
# inserting it into `sys.meta_path`, but I was unable to do that.

import imp
import os
import sys
from grow.common import system

IS_PACKAGED_APP = system.is_packaged_app()
MAC_SYS_PREFIX = '/Library/Frameworks/Python.framework/Versions/3.6/'


# pylint: disable=too-few-public-methods
class FrozenImportFixer(object):
    """
    If importing a module encounters an ImportError, retry importing the
    module by modifying the sys.meta_path. By default, PyInstaller overwrites
    sys.meta_path, this patched object, intended to be used with the `with`
    statement, removes PyInstaller's modifications and reinstates them after
    the import is complete. This should be a no-op outside the frozen
    environment.
    """

    def __init__(self):
        self.frozen_meta_path = None
        self.frozen_sys_path = None

    def __enter__(self):
        if not IS_PACKAGED_APP:
            return
        self.frozen_meta_path = sys.meta_path[:]
        self.frozen_sys_path = sys.path[:]
        if os.path.exists(MAC_SYS_PREFIX):
            sys.path.insert(0, MAC_SYS_PREFIX + '/lib/python2.7')
        sys.meta_path = sys.meta_path[2:]

    def __exit__(self, exc_type, exc_value, traceback):
        if not IS_PACKAGED_APP:
            return
        sys.meta_path = self.frozen_meta_path
        sys.path = self.frozen_sys_path


def _get_module(part1, paths):
    filepath, pathname, description = imp.find_module(part1, paths)
    return imp.load_module(part1, filepath, pathname, description)


def import_extension(name, paths):
    """Imports and returns a module, given its path (e.g. extensions.foo.Bar)."""
    if '.' not in name:
        raise ImportError
    part1, part2 = name.split('.', 1)
    if '.' in part2:
        _, pathname, _ = imp.find_module(part1, paths)
        return import_extension(part2, [pathname])
    if not IS_PACKAGED_APP:
        module = _get_module(part1, paths)
    else:
        original_sys_path = sys.path[:]
        original_sys_prefix = sys.prefix
        if os.path.exists(MAC_SYS_PREFIX):
            sys.prefix = MAC_SYS_PREFIX
        from grow.common import patched_site  # Updates sys.path.
        patched_site.main()
        try:
            module = _get_module(part1, paths)
        except ImportError:
            with FrozenImportFixer():
                module = _get_module(part1, paths)
        # If extension modifies sys.path, preserve the modification.
        sys.prefix = original_sys_prefix
        sys.path = original_sys_path
    result = getattr(module, part2)
    return result
