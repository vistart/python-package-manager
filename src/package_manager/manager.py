"""
Core package manager implementation
"""

import importlib
import inspect
import json
import os
import threading
import warnings
from contextlib import contextmanager
from typing import Dict, List, Optional, Any

from .exceptions import VersionNotFoundError, ImportError
from .version import PackageVersion


class PackageManager:
    """
    Package manager for managing multiple versions of the same package
    """

    def __init__(self, name: str, config_path: str = None, cache_timeout: int = 300):
        """
        Initialize a package manager

        Args:
            name: Name of the package to manage
            config_path: Path to configuration file (default: ~/.{name}_versions.json)
            cache_timeout: Cache timeout in seconds (default: 5 minutes)
        """
        self.name = name
        self.versions: Dict[str, PackageVersion] = {}
        self.active_version: Optional[str] = None
        self.cache_timeout = cache_timeout
        self._lock = threading.RLock()

        # Set default configuration path
        if config_path is None:
            home = os.path.expanduser("~")
            self.config_path = os.path.join(home, f".{name}_versions.json")
        else:
            self.config_path = config_path

        # Load configuration if exists
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)

                # Load versions
                if "versions" in config:
                    for ver_data in config["versions"]:
                        pkg_ver = PackageVersion(
                            name=self.name,
                            version=ver_data["version"],
                            path=ver_data["path"],
                            is_main=ver_data.get("is_main", False),
                            metadata=ver_data.get("metadata", {})
                        )
                        self.versions[ver_data["version"]] = pkg_ver

                # Set active version
                if "active_version" in config and config["active_version"] in self.versions:
                    self.active_version = config["active_version"]
            except Exception as e:
                warnings.warn(f"Failed to load configuration from {self.config_path}: {e}")

    def _save_config(self) -> None:
        """Save configuration to file"""
        config = {
            "name": self.name,
            "active_version": self.active_version,
            "versions": []
        }

        for version, pkg_ver in self.versions.items():
            config["versions"].append({
                "version": version,
                "path": pkg_ver.path,
                "is_main": pkg_ver.is_main,
                "metadata": pkg_ver.metadata
            })

        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            warnings.warn(f"Failed to save configuration to {self.config_path}: {e}")

    def register_main_version(self) -> Optional[PackageVersion]:
        """
        Register the main pip-installed version of the package

        Returns:
            PackageVersion if successful, None if not found
        """
        with self._lock:
            try:
                # Try to find the package in sys.path
                module = importlib.import_module(self.name)
                path = os.path.dirname(inspect.getfile(module))

                # Try to get version
                version = getattr(module, "__version__", "main")

                pkg_ver = PackageVersion(
                    name=self.name,
                    version=version,
                    path=path,
                    is_main=True
                )

                self.versions[version] = pkg_ver

                # If no active version, set this as active
                if self.active_version is None:
                    self.active_version = version

                self._save_config()
                return pkg_ver
            except ImportError:
                return None

    def register_version(self, version: str, path: str, metadata: Dict[str, Any] = None) -> PackageVersion:
        """
        Register a specific version of the package

        Args:
            version: Version string
            path: Path to the package
            metadata: Additional metadata

        Returns:
            The registered PackageVersion
        """
        with self._lock:
            # Check if path exists
            if not os.path.exists(path):
                raise ValueError(f"Path does not exist: {path}")

            pkg_ver = PackageVersion(
                name=self.name,
                version=version,
                path=path,
                is_main=False,
                metadata=metadata
            )

            # Try to load to verify it's valid
            try:
                pkg_ver.load()
            except Exception as e:
                raise ValueError(f"Failed to load package at {path}: {e}")

            self.versions[version] = pkg_ver

            # If no active version, set this as active
            if self.active_version is None:
                self.active_version = version

            self._save_config()
            return pkg_ver

    def unregister_version(self, version: str) -> bool:
        """
        Unregister a specific version

        Args:
            version: Version to unregister

        Returns:
            True if successful, False if version not found
        """
        with self._lock:
            if version not in self.versions:
                return False

            # Check if it's the active version
            if self.active_version == version:
                # Find another version to make active
                other_versions = [v for v in self.versions if v != version]
                if other_versions:
                    self.active_version = other_versions[0]
                else:
                    self.active_version = None

            del self.versions[version]
            self._save_config()
            return True

    def use_version(self, version: str) -> Any:
        """
        Set and load a specific version as active

        Args:
            version: Version to use

        Returns:
            The loaded module
        """
        with self._lock:
            if version not in self.versions:
                raise VersionNotFoundError(self.name, version)

            self.active_version = version
            self._save_config()
            return self.versions[version].load()

    def get_version(self, version: str = None) -> Any:
        """
        Get a specific version without changing the active version

        Args:
            version: Version to get, or None for active version

        Returns:
            The loaded module
        """
        version = version or self.active_version
        if version is None:
            raise ValueError("No active version set and no version specified")

        if version not in self.versions:
            raise VersionNotFoundError(self.name, version)

        return self.versions[version].load()

    @contextmanager
    def temporary_version(self, version: str):
        """
        Temporarily use a specific version in a context

        Args:
            version: Version to use temporarily

        Yields:
            The loaded module
        """
        if version not in self.versions:
            raise VersionNotFoundError(self.name, version)

        with self._lock:
            old_version = self.active_version
            self.active_version = version

            try:
                yield self.versions[version].load()
            finally:
                self.active_version = old_version

    def list_versions(self) -> List[Dict[str, Any]]:
        """
        List all registered versions

        Returns:
            List of version information dictionaries
        """
        result = []
        for version, pkg_ver in self.versions.items():
            info = pkg_ver.get_info()
            info["active"] = (version == self.active_version)
            result.append(info)

        return result

    def get_active_version(self) -> Optional[PackageVersion]:
        """
        Get the currently active version

        Returns:
            The active PackageVersion or None if no active version
        """
        if self.active_version is None:
            return None

        return self.versions.get(self.active_version)

    def __call__(self) -> Any:
        """
        Get the active version module when the manager is called

        Returns:
            The active version module
        """
        if self.active_version is None:
            raise ValueError("No active version set")

        return self.versions[self.active_version].load()