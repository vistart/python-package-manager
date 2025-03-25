"""
Tests for the PackageManager class.
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from src.package_manager.manager import PackageManager
from src.package_manager.version import PackageVersion
from src.package_manager.exceptions import VersionNotFoundError


class TestPackageManager:
    """Tests for PackageManager class"""

    def test_init(self):
        """Test initialization"""
        with tempfile.NamedTemporaryFile() as temp_file:
            manager = PackageManager("requests", config_path=temp_file.name)

            assert manager.name == "requests"
            assert manager.config_path == temp_file.name
            assert manager.versions == {}
            assert manager.active_version is None
            assert manager.cache_timeout == 300

    def test_load_save_config(self):
        """Test loading and saving configuration"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Create a test configuration
            config = {
                "name": "requests",
                "active_version": "2.25.1",
                "versions": [
                    {
                        "version": "2.25.1",
                        "path": "/path/to/requests",
                        "is_main": True,
                        "metadata": {"key": "value"}
                    }
                ]
            }
            temp_file.write(json.dumps(config).encode('utf-8'))
            temp_file.flush()

            # Test loading
            manager = PackageManager("requests", config_path=temp_file.name)
            assert "2.25.1" in manager.versions
            assert manager.active_version == "2.25.1"
            assert manager.versions["2.25.1"].path == "/path/to/requests"
            assert manager.versions["2.25.1"].is_main is True
            assert manager.versions["2.25.1"].metadata == {"key": "value"}

            # Test saving
            manager.versions["2.26.0"] = PackageVersion(
                "requests",
                "2.26.0",
                "/path/to/new/requests",
                is_main=False
            )
            manager.active_version = "2.26.0"
            manager._save_config()

            # Verify new config
            with open(temp_file.name, 'r') as f:
                saved_config = json.load(f)

            assert saved_config["active_version"] == "2.26.0"
            assert len(saved_config["versions"]) == 2
            assert any(v["version"] == "2.26.0" for v in saved_config["versions"])

        # Clean up
        os.unlink(temp_file.name)

    def test_register_main_version(self):
        """Test registering main version"""
        manager = PackageManager("pytest")

        # Mock importlib.import_module
        mock_module = MagicMock()
        mock_module.__version__ = "7.0.0"

        with patch('inspect.getfile', return_value="/path/to/pytest/__init__.py"):
            with patch('importlib.import_module', return_value=mock_module):
                result = manager.register_main_version()

                assert result is not None
                assert result.name == "pytest"
                assert result.version == "7.0.0"
                assert result.path == "/path/to/pytest"
                assert result.is_main is True
                assert "7.0.0" in manager.versions
                assert manager.active_version == "7.0.0"

    def test_unregister_version(self):
        """Test unregistering a version"""
        manager = PackageManager("requests")

        # Add some test versions
        manager.versions["2.25.1"] = PackageVersion("requests", "2.25.1", "/path/1", is_main=True)
        manager.versions["2.26.0"] = PackageVersion("requests", "2.26.0", "/path/2", is_main=False)
        manager.active_version = "2.25.1"

        # Test unregistering non-active version
        result = manager.unregister_version("2.26.0")
        assert result is True
        assert "2.26.0" not in manager.versions
        assert manager.active_version == "2.25.1"

        # Test unregistering active version
        result = manager.unregister_version("2.25.1")
        assert result is True
        assert "2.25.1" not in manager.versions
        assert manager.active_version is None

        # Test unregistering non-existent version
        result = manager.unregister_version("nonexistent")
        assert result is False

    def test_use_version(self):
        """Test setting and loading active version"""
        manager = PackageManager("requests")

        # Create mock versions
        ver1 = PackageVersion("requests", "2.25.1", "/path/1", is_main=True)
        ver2 = PackageVersion("requests", "2.26.0", "/path/2", is_main=False)

        # Add to manager
        manager.versions["2.25.1"] = ver1
        manager.versions["2.26.0"] = ver2

        # Mock load method
        mock_module1 = MagicMock()
        mock_module2 = MagicMock()

        with patch.object(ver1, 'load', return_value=mock_module1):
            with patch.object(ver2, 'load', return_value=mock_module2):
                # Test using valid version
                result = manager.use_version("2.25.1")
                assert result == mock_module1
                assert manager.active_version == "2.25.1"

                # Switch to another version
                result = manager.use_version("2.26.0")
                assert result == mock_module2
                assert manager.active_version == "2.26.0"

                # Test using non-existent version
                with pytest.raises(VersionNotFoundError):
                    manager.use_version("nonexistent")

    def test_get_version(self):
        """Test getting a version without changing active version"""
        manager = PackageManager("requests")

        # Create mock versions
        ver1 = PackageVersion("requests", "2.25.1", "/path/1", is_main=True)
        ver2 = PackageVersion("requests", "2.26.0", "/path/2", is_main=False)

        # Add to manager
        manager.versions["2.25.1"] = ver1
        manager.versions["2.26.0"] = ver2
        manager.active_version = "2.25.1"

        # Mock load method
        mock_module1 = MagicMock()
        mock_module2 = MagicMock()

        with patch.object(ver1, 'load', return_value=mock_module1):
            with patch.object(ver2, 'load', return_value=mock_module2):
                # Test getting active version
                result = manager.get_version()
                assert result == mock_module1
                assert manager.active_version == "2.25.1"  # Unchanged

                # Test getting specific version
                result = manager.get_version("2.26.0")
                assert result == mock_module2
                assert manager.active_version == "2.25.1"  # Still unchanged

                # Test with no active version
                manager.active_version = None
                with pytest.raises(ValueError):
                    manager.get_version()

                # Test getting non-existent version
                with pytest.raises(VersionNotFoundError):
                    manager.get_version("nonexistent")

    def test_temporary_version(self):
        """Test temporarily using a specific version"""
        manager = PackageManager("requests")

        # Create mock versions
        ver1 = PackageVersion("requests", "2.25.1", "/path/1", is_main=True)
        ver2 = PackageVersion("requests", "2.26.0", "/path/2", is_main=False)

        # Add to manager
        manager.versions["2.25.1"] = ver1
        manager.versions["2.26.0"] = ver2
        manager.active_version = "2.25.1"

        # Mock load method
        mock_module1 = MagicMock()
        mock_module2 = MagicMock()

        with patch.object(ver1, 'load', return_value=mock_module1):
            with patch.object(ver2, 'load', return_value=mock_module2):
                # Test context manager
                with manager.temporary_version("2.26.0") as module:
                    assert module == mock_module2
                    assert manager.active_version == "2.26.0"

                # After context, should be back to previous
                assert manager.active_version == "2.25.1"

                # Test with non-existent version
                with pytest.raises(VersionNotFoundError):
                    with manager.temporary_version("nonexistent"):
                        pass

                # Test exception inside context
                try:
                    with manager.temporary_version("2.26.0"):
                        assert manager.active_version == "2.26.0"
                        raise ValueError("Test error")
                except ValueError:
                    pass

                # Should still restore previous version
                assert manager.active_version == "2.25.1"

    def test_list_versions(self):
        """Test listing all versions"""
        manager = PackageManager("requests")

        # Create mock versions
        ver1 = PackageVersion("requests", "2.25.1", "/path/1", is_main=True)
        ver2 = PackageVersion("requests", "2.26.0", "/path/2", is_main=False)

        # Add to manager
        manager.versions["2.25.1"] = ver1
        manager.versions["2.26.0"] = ver2
        manager.active_version = "2.25.1"

        # Mock get_info method
        with patch.object(ver1, 'get_info', return_value={"name": "requests", "version": "2.25.1"}):
            with patch.object(ver2, 'get_info', return_value={"name": "requests", "version": "2.26.0"}):
                result = manager.list_versions()

                assert len(result) == 2
                assert result[0]["version"] == "2.25.1"
                assert result[0]["active"] is True
                assert result[1]["version"] == "2.26.0"
                assert result[1]["active"] is False

    def test_get_active_version(self):
        """Test getting active version"""
        manager = PackageManager("requests")

        # No active version
        assert manager.get_active_version() is None

        # With active version
        test_ver = PackageVersion("requests", "2.25.1", "/path", is_main=True)
        manager.versions["2.25.1"] = test_ver
        manager.active_version = "2.25.1"

        assert manager.get_active_version() == test_ver

    def test_call(self):
        """Test calling the manager"""
        manager = PackageManager("requests")

        # No active version
        with pytest.raises(ValueError):
            manager()

        # With active version
        test_ver = PackageVersion("requests", "2.25.1", "/path", is_main=True)
        manager.versions["2.25.1"] = test_ver
        manager.active_version = "2.25.1"

        mock_module = MagicMock()
        with patch.object(test_ver, 'load', return_value=mock_module):
            result = manager()
            assert result == mock_module