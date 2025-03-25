"""
Tests for the exceptions module.
"""
import pytest

from src.package_manager.exceptions import (
    PackageManagerError,
    PackageNotFoundError,
    VersionNotFoundError,
    ImportError,
    ConfigError
)


class TestExceptions:
    """Tests for exception classes"""

    def test_package_manager_error(self):
        """Test PackageManagerError base exception"""
        error = PackageManagerError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_package_not_found_error(self):
        """Test PackageNotFoundError"""
        error = PackageNotFoundError("requests")
        assert str(error) == "Package not found: requests"
        assert error.package_name == "requests"
        assert isinstance(error, PackageManagerError)

    def test_version_not_found_error(self):
        """Test VersionNotFoundError"""
        error = VersionNotFoundError("requests", "2.25.1")
        assert str(error) == "Version 2.25.1 not found for package requests"
        assert error.package_name == "requests"
        assert error.version == "2.25.1"
        assert isinstance(error, PackageManagerError)

    def test_import_error(self):
        """Test ImportError"""
        error = ImportError("Failed to import module")
        assert str(error) == "Failed to import module"
        assert isinstance(error, PackageManagerError)

    def test_config_error(self):
        """Test ConfigError"""
        error = ConfigError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, PackageManagerError)

    def test_exception_hierarchy(self):
        """Test exception hierarchy"""
        # All should inherit from PackageManagerError
        assert issubclass(PackageNotFoundError, PackageManagerError)
        assert issubclass(VersionNotFoundError, PackageManagerError)
        assert issubclass(ImportError, PackageManagerError)
        assert issubclass(ConfigError, PackageManagerError)

        # Should not inherit from each other
        assert not issubclass(PackageNotFoundError, VersionNotFoundError)
        assert not issubclass(VersionNotFoundError, ImportError)
        assert not issubclass(ImportError, ConfigError)