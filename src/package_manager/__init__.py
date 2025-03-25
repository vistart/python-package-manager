"""
PackageManager - A Python3 package version manager that allows managing
multiple versions of the same package simultaneously.

Features:
- Main version management (pip installed)
- Registration of alternative versions
- Version switching (active version concept)
- Context-based temporary version usage
- Caching mechanism
- Information and listing features
"""

__version__ = "1.0.0.dev1"
__author__ = "vistart"

# Import public classes and functions
from .version import PackageVersion
from .manager import PackageManager
from .registry import get_package_manager, _package_managers
from .utils import setup_package_manager, import_version, create_decorator
from .exceptions import PackageManagerError, PackageNotFoundError, VersionNotFoundError

# Define public API
__all__ = [
    'PackageVersion',
    'PackageManager',
    'get_package_manager',
    'setup_package_manager',
    'import_version',
    'create_decorator',
    'PackageManagerError',
    'PackageNotFoundError',
    'VersionNotFoundError',
]