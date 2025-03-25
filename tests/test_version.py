"""
Tests for the PackageVersion class.
"""
import os
import sys
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from src.package_manager.version import PackageVersion
from src.package_manager.exceptions import ImportError


class TestPackageVersion:
    """Tests for PackageVersion class"""

    def test_init(self):
        """Test PackageVersion initialization"""
        pkg_ver = PackageVersion("test_pkg", "1.0.0", "/path/to/pkg", is_main=True,
                                metadata={"key": "value"})

        assert pkg_ver.name == "test_pkg"
        assert pkg_ver.version == "1.0.0"
        assert pkg_ver.path == "/path/to/pkg"
        assert pkg_ver.is_main is True
        assert pkg_ver.metadata == {"key": "value"}
        assert pkg_ver._module is None
        assert pkg_ver._last_loaded == 0

    def test_repr(self):
        """Test string representation"""
        pkg_ver1 = PackageVersion("test_pkg", "1.0.0", "/path", is_main=True)
        pkg_ver2 = PackageVersion("test_pkg", "2.0.0", "/path", is_main=False)

        assert repr(pkg_ver1) == "<PackageVersion test_pkg:1.0.0 (main)>"
        assert repr(pkg_ver2) == "<PackageVersion test_pkg:2.0.0 >"

    def test_load_main_version(self):
        """Test loading main package version"""
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_import.return_value = mock_module

            pkg_ver = PackageVersion("pytest", "main", "", is_main=True)
            result = pkg_ver.load()

            mock_import.assert_called_once_with("pytest")
            assert result == mock_module
            assert pkg_ver._module == mock_module
            assert pkg_ver._last_loaded > 0

    def test_load_main_version_error(self):
        """Test error handling when loading main version fails"""
        with patch('importlib.import_module', side_effect=Exception("Test error")):
            pkg_ver = PackageVersion("nonexistent_pkg", "main", "", is_main=True)

            with pytest.raises(ImportError) as exc_info:
                pkg_ver.load()

            assert "Failed to import main package nonexistent_pkg" in str(exc_info.value)

    def test_load_custom_version_directory(self):
        """Test loading a custom version from a directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package structure
            pkg_dir = os.path.join(temp_dir, "test_pkg")
            os.makedirs(pkg_dir)

            # Create an __init__.py file
            with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
                f.write("__version__ = '1.0.0'\n")

            pkg_ver = PackageVersion("test_pkg", "1.0.0", pkg_dir, is_main=False)

            # Mock spec creation to avoid actual import
            with patch('importlib.util.spec_from_file_location') as mock_spec_from_file_location:
                mock_spec = MagicMock()
                mock_loader = MagicMock()
                mock_spec.loader = mock_loader
                mock_spec.name = "test_pkg_1.0.0"
                mock_spec_from_file_location.return_value = mock_spec

                with patch('importlib.util.module_from_spec') as mock_module_from_spec:
                    mock_module = MagicMock()
                    mock_module.__version__ = "1.0.0"
                    mock_module_from_spec.return_value = mock_module

                    result = pkg_ver.load()

                    # Check the right path was used
                    mock_spec_from_file_location.assert_called_once_with(
                        "test_pkg_1.0.0",
                        os.path.join(pkg_dir, "__init__.py")
                    )
                    mock_module_from_spec.assert_called_once_with(mock_spec)
                    mock_loader.exec_module.assert_called_once_with(mock_module)
                    assert result == mock_module
                    assert pkg_ver._module == mock_module

    def test_load_custom_version_file(self):
        """Test loading a custom version from a file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a single module file
            module_file = os.path.join(temp_dir, "test_module.py")
            with open(module_file, "w") as f:
                f.write("__version__ = '1.0.0'\n")

            pkg_ver = PackageVersion("test_module", "1.0.0", module_file, is_main=False)

            # Mock spec creation to avoid actual import
            with patch('importlib.util.spec_from_file_location') as mock_spec_from_file_location:
                mock_spec = MagicMock()
                mock_loader = MagicMock()
                mock_spec.loader = mock_loader
                mock_spec.name = "test_module_1.0.0"
                mock_spec_from_file_location.return_value = mock_spec

                with patch('importlib.util.module_from_spec') as mock_module_from_spec:
                    mock_module = MagicMock()
                    mock_module.__version__ = "1.0.0"
                    mock_module_from_spec.return_value = mock_module

                    result = pkg_ver.load()

                    # Check the right path was used
                    mock_spec_from_file_location.assert_called_once_with(
                        "test_module_1.0.0",
                        module_file
                    )
                    assert result == mock_module

    def test_load_custom_version_error(self):
        """Test error handling when loading custom version fails"""
        pkg_ver = PackageVersion("test_pkg", "1.0.0", "/nonexistent/path", is_main=False)

        with pytest.raises(ImportError) as exc_info:
            pkg_ver.load()

        assert "Failed to import package test_pkg" in str(exc_info.value)

    def test_get_info(self):
        """Test getting package information"""
        pkg_ver = PackageVersion("test_pkg", "1.0.0", "/path", is_main=True,
                                metadata={"key": "value"})

        # Mock the load method
        mock_module = MagicMock()
        mock_module.__version__ = "1.0.0"
        mock_module.__author__ = "Test Author"
        mock_module.__doc__ = "Test documentation"

        with patch.object(pkg_ver, 'load', return_value=mock_module):
            info = pkg_ver.get_info()

            assert info["name"] == "test_pkg"
            assert info["version"] == "1.0.0"
            assert info["path"] == "/path"
            assert info["is_main"] is True
            assert info["metadata"] == {"key": "value"}
            assert info["actual_version"] == "1.0.0"
            assert info["author"] == "Test Author"
            assert info["doc"] == "Test documentation"

    def test_get_info_error(self):
        """Test getting info when loading fails"""
        pkg_ver = PackageVersion("test_pkg", "1.0.0", "/path", is_main=True)

        # Mock the load method to raise an exception
        with patch.object(pkg_ver, 'load', side_effect=Exception("Test error")):
            info = pkg_ver.get_info()

            # Should still return basic info
            assert info["name"] == "test_pkg"
            assert info["version"] == "1.0.0"
            assert info["path"] == "/path"
            assert info["is_main"] is True
            assert "actual_version" not in info
            assert "author" not in info
            assert "doc" not in info

    def test_cache_behavior(self):
        """Test caching behavior"""
        pkg_ver = PackageVersion("test_pkg", "1.0.0", "/path", is_main=True)

        # Mock load functionality
        mock_module = MagicMock()
        with patch('importlib.import_module', return_value=mock_module) as mock_import:
            # First load
            result1 = pkg_ver.load()
            assert result1 == mock_module
            assert pkg_ver._module == mock_module
            mock_import.assert_called_once_with("test_pkg")

            # Second load should use cache
            mock_import.reset_mock()
            result2 = pkg_ver.load()
            assert result2 == mock_module
            mock_import.assert_not_called()

            # Force reload
            mock_import.reset_mock()
            result3 = pkg_ver.load(force=True)
            assert result3 == mock_module
            mock_import.assert_called_once_with("test_pkg")