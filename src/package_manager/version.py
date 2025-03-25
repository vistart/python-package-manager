"""
Module for package version representation
"""

import importlib
import importlib.util
import os
import sys
import time
import logging
from typing import Dict, Any

from .exceptions import ImportError

# Setup logging
logger = logging.getLogger("package_manager")

class PackageVersion:
    """Represents a single package version"""

    def __init__(self, name: str, version: str, path: str, is_main: bool = False,
                 metadata: Dict[str, Any] = None):
        """
        Initialize a package version

        Args:
            name: Package name
            version: Version string
            path: Path to the package
            is_main: Whether this is the main (pip) version
            metadata: Additional metadata for the package
        """
        self.name = name
        self.version = version
        self.path = path
        self.is_main = is_main
        self.metadata = metadata or {}
        self._module = None
        self._last_loaded = 0

    def __repr__(self) -> str:
        return f"<PackageVersion {self.name}:{self.version} {'(main)' if self.is_main else ''}>"

    def load(self, force: bool = False) -> Any:
        """
        Load the package module

        Args:
            force: Force reload even if cached

        Returns:
            The loaded module
        """
        now = time.time()
        if self._module is not None and not force and (now - self._last_loaded) < 300:  # 5 min cache
            return self._module

        if self.is_main:
            try:
                if self._module is not None and force:
                    if hasattr(self._module, "__file__") and self._module.__file__ is not None:
                        # Force reload by removing from sys.modules
                        name = self._module.__name__
                        if name in sys.modules:
                            del sys.modules[name]

                self._module = importlib.import_module(self.name)
            except Exception as e:
                raise ImportError(f"Failed to import main package {self.name}: {e}")
        else:
            try:
                # Debug information about the path being processed
                logger.debug(f"Loading package {self.name} version {self.version} from path: {self.path}")
                logger.debug(f"Path exists: {os.path.exists(self.path)}")
                logger.debug(f"Path is directory: {os.path.isdir(self.path)}")

                # Comprehensive check if path is directory or file
                if os.path.exists(self.path) and os.path.isdir(self.path):
                    # Path is an existing directory
                    init_path = os.path.join(self.path, "__init__.py")
                    logger.debug(f"Looking for __init__.py at: {init_path}")
                    logger.debug(f"__init__.py exists: {os.path.exists(init_path)}")

                    # Verify __init__.py file exists
                    if not os.path.exists(init_path):
                        raise ImportError(f"No __init__.py found at {init_path}")

                    spec = importlib.util.spec_from_file_location(
                        f"{self.name}_{self.version}",
                        init_path
                    )

                    if spec is None:
                        raise ImportError(f"Could not create module spec from {init_path}")

                elif os.path.exists(f"{self.path}.py"):
                    # Path is a file without .py extension
                    logger.debug(f"Found module file at: {self.path}.py")
                    spec = importlib.util.spec_from_file_location(
                        f"{self.name}_{self.version}",
                        f"{self.path}.py"
                    )

                    if spec is None:
                        raise ImportError(f"Could not create module spec from {self.path}.py")

                elif os.path.exists(self.path) and self.path.endswith(".py"):
                    # Path is a file with .py extension
                    logger.debug(f"Using module file: {self.path}")
                    spec = importlib.util.spec_from_file_location(
                        f"{self.name}_{self.version}",
                        self.path
                    )

                    if spec is None:
                        raise ImportError(f"Could not create module spec from {self.path}")

                elif os.path.exists(os.path.join(os.path.dirname(self.path), f"{os.path.basename(self.path)}.py")):
                    # Path might be part of directory name, try to treat it as a filename
                    file_path = os.path.join(os.path.dirname(self.path), f"{os.path.basename(self.path)}.py")
                    logger.debug(f"Found module file in parent directory: {file_path}")
                    spec = importlib.util.spec_from_file_location(
                        f"{self.name}_{self.version}",
                        file_path
                    )

                    if spec is None:
                        raise ImportError(f"Could not create module spec from {file_path}")

                elif os.path.exists(os.path.join(os.path.dirname(self.path), os.path.basename(self.path), "__init__.py")):
                    # Path might be a parent directory containing __init__.py
                    init_path = os.path.join(os.path.dirname(self.path), os.path.basename(self.path), "__init__.py")
                    logger.debug(f"Found __init__.py in subdirectory: {init_path}")
                    spec = importlib.util.spec_from_file_location(
                        f"{self.name}_{self.version}",
                        init_path
                    )

                    if spec is None:
                        raise ImportError(f"Could not create module spec from {init_path}")

                else:
                    # Try to import as package directly
                    logger.debug(f"Trying to import as package: {self.name}")
                    try:
                        package_name = os.path.basename(self.path)
                        sys.path.insert(0, os.path.dirname(self.path))
                        self._module = importlib.import_module(package_name)
                        sys.path.pop(0)
                        self._last_loaded = now
                        return self._module
                    except Exception as e:
                        # List directory contents for debugging
                        try:
                            if os.path.exists(os.path.dirname(self.path)):
                                logger.debug(f"Contents of parent directory {os.path.dirname(self.path)}: {os.listdir(os.path.dirname(self.path))}")
                            if os.path.exists(self.path):
                                logger.debug(f"Contents of directory {self.path}: {os.listdir(self.path)}")
                        except Exception as list_err:
                            logger.debug(f"Failed to list directory contents: {list_err}")

                        raise ImportError(
                            f"Could not find valid module or package at {self.path}. "
                            f"Path exists: {os.path.exists(self.path)}. "
                            f"Path is directory: {os.path.isdir(self.path) if os.path.exists(self.path) else 'N/A'}. "
                            f"Import error: {e}"
                        )

                # Load module using spec
                module = importlib.util.module_from_spec(spec)
                # Add module to sys.modules to handle relative imports
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                self._module = module

            except Exception as e:
                # Detailed error information
                error_msg = f"Failed to import package {self.name} version {self.version} from {self.path}: {e}"
                logger.error(error_msg)
                logger.error(f"Path exists: {os.path.exists(self.path)}")
                if os.path.exists(self.path) and os.path.isdir(self.path):
                    logger.error(f"Directory content: {os.listdir(self.path)}")
                    init_file = os.path.join(self.path, "__init__.py")
                    logger.error(f"__init__.py exists: {os.path.exists(init_file)}")

                raise ImportError(error_msg)

        self._last_loaded = now
        return self._module

    def get_info(self) -> Dict[str, Any]:
        """
        Get package information

        Returns:
            Dict with package information
        """
        info = {
            "name": self.name,
            "version": self.version,
            "path": self.path,
            "is_main": self.is_main,
            "metadata": self.metadata,
        }

        # Try to get additional info from the module
        try:
            module = self.load()
            if hasattr(module, "__version__"):
                info["actual_version"] = module.__version__
            if hasattr(module, "__author__"):
                info["author"] = module.__author__
            if hasattr(module, "__doc__"):
                info["doc"] = module.__doc__
        except Exception:
            # Ignore errors when trying to get additional info
            pass

        return info