"""
Utility functions for package manager
"""

import warnings
from typing import Dict, Any, Union

from .registry import get_package_manager
from .exceptions import VersionNotFoundError


def setup_package_manager(name: str, register_main: bool = True,
                          versions: Dict[str, Union[str, Dict[str, Any]]] = None,
                          default_version: str = None,
                          **kwargs) -> 'PackageManager':
    """
    Set up a package manager with initial configuration

    Args:
        name: Package name
        register_main: Whether to register the main pip version
        versions: Dictionary of version names to paths or {path, metadata} dicts
        default_version: Default version to set as active
        **kwargs: Additional arguments to pass to PackageManager constructor

    Returns:
        The configured PackageManager
    """
    manager = get_package_manager(name, **kwargs)

    # Register main version if requested
    if register_main:
        main_ver = manager.register_main_version()
        if main_ver is None:
            warnings.warn(f"Main version of {name} not found in pip packages")

    # Register additional versions
    if versions:
        for version, path_or_dict in versions.items():
            if isinstance(path_or_dict, str):
                manager.register_version(version, path_or_dict)
            else:
                manager.register_version(
                    version,
                    path_or_dict["path"],
                    metadata=path_or_dict.get("metadata")
                )

    # Set default version if specified
    if default_version:
        if default_version in manager.versions:
            manager.use_version(default_version)
        else:
            warnings.warn(f"Default version {default_version} not found in registered versions")

    return manager


def import_version(package_name: str, version: str = None) -> Any:
    """
    Import a specific version of a package

    Args:
        package_name: Package name
        version: Version to import, or None for active version

    Returns:
        The loaded module
    """
    manager = get_package_manager(package_name)
    return manager.get_version(version)


def create_decorator(package_name: str, version: str):
    """
    Create a decorator to use a specific package version in a function

    Args:
        package_name: Package name
        version: Version to use

    Returns:
        A decorator function
    """
    manager = get_package_manager(package_name)

    if version not in manager.versions:
        raise VersionNotFoundError(package_name, version)

    def decorator(func):
        import functools
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with manager.temporary_version(version):
                return func(*args, **kwargs)

        return wrapper

    return decorator