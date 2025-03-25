"""
Tests for utility functions.
"""
import pytest
from unittest.mock import patch, MagicMock

from src.package_manager.utils import setup_package_manager, import_version, create_decorator
from src.package_manager.manager import PackageManager
from src.package_manager.exceptions import VersionNotFoundError


class TestUtils:
    """Tests for utility functions"""

    def test_setup_package_manager(self):
        """Test setup_package_manager function"""
        # Mock get_package_manager
        mock_manager = MagicMock(spec=PackageManager)
        mock_manager.versions = {}

        with patch('src.package_manager.utils.get_package_manager', return_value=mock_manager) as mock_get_manager:
            # Test with register_main=True
            result = setup_package_manager(
                "pytest",
                register_main=True,
                versions={
                    "custom": "/path/to/custom",
                    "special": {
                        "path": "/path/to/special",
                        "metadata": {"key": "value"}
                    }
                },
                default_version="custom"
            )

            # Verify calls
            mock_get_manager.assert_called_once_with("pytest")
            mock_manager.register_main_version.assert_called_once()
            assert mock_manager.register_version.call_count == 2

            # Check register version calls
            mock_manager.register_version.assert_any_call("custom", "/path/to/custom")
            mock_manager.register_version.assert_any_call("special", "/path/to/special", metadata={"key": "value"})

            # Check default version
            mock_manager.use_version.assert_called_once_with("custom")

            assert result == mock_manager

    def test_setup_package_manager_no_default(self):
        """Test setup_package_manager with non-existent default"""
        # Mock get_package_manager
        mock_manager = MagicMock(spec=PackageManager)
        mock_manager.versions = {}

        # Mock register_version to add to versions
        def mock_register(version, path, metadata=None):
            mock_manager.versions[version] = True
            return MagicMock()

        mock_manager.register_version.side_effect = mock_register

        with patch('src.package_manager.utils.get_package_manager', return_value=mock_manager):
            with patch('src.package_manager.utils.warnings') as mock_warnings:
                # Test with non-existent default
                setup_package_manager(
                    "pytest",
                    register_main=False,
                    versions={"custom": "/path/to/custom"},
                    default_version="nonexistent"
                )

                # Should show warning
                mock_warnings.warn.assert_called_once()

    def test_import_version(self):
        """Test import_version function"""
        # Mock get_package_manager
        mock_manager = MagicMock(spec=PackageManager)
        mock_module = MagicMock()
        mock_manager.get_version.return_value = mock_module

        with patch('src.package_manager.utils.get_package_manager', return_value=mock_manager) as mock_get_manager:
            # Test with specific version
            result = import_version("pytest", "7.0.0")

            mock_get_manager.assert_called_once_with("pytest")
            mock_manager.get_version.assert_called_once_with("7.0.0")
            assert result == mock_module

            # Test with default version
            mock_get_manager.reset_mock()
            mock_manager.get_version.reset_mock()

            result = import_version("pytest")

            mock_get_manager.assert_called_once_with("pytest")
            mock_manager.get_version.assert_called_once_with(None)
            assert result == mock_module

    def test_create_decorator(self):
        """Test create_decorator function"""
        # Mock get_package_manager
        mock_manager = MagicMock(spec=PackageManager)
        mock_manager.versions = {"7.0.0": True}

        # Create a mock context manager
        @patch('src.package_manager.utils.get_package_manager', return_value=mock_manager)
        def test_decorator(mock_get_manager):
            # Create the decorator
            decorator = create_decorator("pytest", "7.0.0")

            # Create a test function
            @decorator
            def test_func(arg1, arg2=None):
                return f"Result: {arg1}, {arg2}"

            # Call the decorated function
            result = test_func("test", arg2="value")

            # Verify context manager was used
            mock_manager.temporary_version.assert_called_once_with("7.0.0")
            assert result == "Result: test, value"

            # Test with non-existent version
            mock_manager.versions = {}
            with pytest.raises(VersionNotFoundError):
                create_decorator("pytest", "nonexistent")

        # Run the test
        test_decorator()

    def test_decorator_preserves_metadata(self):
        """Test that decorator preserves function metadata"""
        # Mock get_package_manager
        mock_manager = MagicMock(spec=PackageManager)
        mock_manager.versions = {"7.0.0": True}

        with patch('src.package_manager.utils.get_package_manager', return_value=mock_manager):
            # Create the decorator
            decorator = create_decorator("pytest", "7.0.0")

            # Create a test function with docstring and metadata
            @decorator
            def test_func():
                """Test docstring"""
                return "result"

            # Check that metadata is preserved
            assert test_func.__name__ == "test_func"
            assert test_func.__doc__ == "Test docstring"