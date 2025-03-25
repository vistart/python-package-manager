"""
Tests for the registry module.
"""
import pytest
from unittest.mock import patch, MagicMock

from src.package_manager.registry import get_package_manager, _package_managers


class TestRegistry:
    """Tests for registry module"""

    def test_get_package_manager(self):
        """Test get_package_manager function"""
        # Clear the registry
        _package_managers.clear()

        # Mock PackageManager
        mock_manager = MagicMock()

        with patch('src.package_manager.registry.PackageManager', return_value=mock_manager) as mock_init:
            # First call should create a new manager
            manager1 = get_package_manager("test_pkg", option1="value1")

            mock_init.assert_called_once_with("test_pkg", option1="value1")
            assert manager1 == mock_manager
            assert "test_pkg" in _package_managers
            assert _package_managers["test_pkg"] == mock_manager

            # Second call should return existing manager
            mock_init.reset_mock()
            manager2 = get_package_manager("test_pkg", option2="value2")

            mock_init.assert_not_called()  # Should not create a new one
            assert manager2 == mock_manager
            assert manager2 is manager1  # Should be the same object

            # Different package should create a new manager
            mock_init.reset_mock()
            new_mock_manager = MagicMock()
            mock_init.return_value = new_mock_manager

            manager3 = get_package_manager("other_pkg")

            mock_init.assert_called_once_with("other_pkg")
            assert manager3 == new_mock_manager
            assert "other_pkg" in _package_managers
            assert _package_managers["other_pkg"] == new_mock_manager

    def test_registry_singleton_behavior(self):
        """Test that the registry acts as a singleton for package managers"""
        # Clear the registry
        _package_managers.clear()

        # Create managers for a couple of packages
        with patch('src.package_manager.registry.PackageManager') as mock_init:
            mock_init.side_effect = lambda name, **kwargs: MagicMock(name=name, **kwargs)

            pkg1_manager = get_package_manager("pkg1")
            pkg2_manager = get_package_manager("pkg2")

            # Should create separate managers
            assert pkg1_manager != pkg2_manager
            assert pkg1_manager.name == "pkg1"
            assert pkg2_manager.name == "pkg2"

            # Getting the same package again should return the same manager
            pkg1_again = get_package_manager("pkg1")
            assert pkg1_again is pkg1_manager

            # Registry should contain both managers
            assert "pkg1" in _package_managers
            assert "pkg2" in _package_managers
            assert len(_package_managers) == 2