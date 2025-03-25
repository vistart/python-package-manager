"""
Global registry for package managers
"""

from typing import Dict

# Global registry of package managers
_package_managers: Dict[str, 'PackageManager'] = {}


def get_package_manager(name: str, **kwargs) -> 'PackageManager':
    """
    Get or create a package manager for the given package name

    Args:
        name: Package name
        **kwargs: Additional arguments to pass to PackageManager constructor

    Returns:
        A PackageManager instance
    """
    if name not in _package_managers:
        # Import here to avoid circular imports
        from .manager import PackageManager
        _package_managers[name] = PackageManager(name, **kwargs)
    return _package_managers[name]