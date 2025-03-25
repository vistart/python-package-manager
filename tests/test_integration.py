"""
Integration tests for package_manager.
Uses installed packages and downloads additional versions from PyPI.
"""
import importlib
import os
import subprocess
import sys
import tempfile
import zipfile

import pkg_resources
import pytest
import requests

# Import package_manager components
from src.package_manager import setup_package_manager, import_version, create_decorator


class TestIntegration:
    """Integration tests using real packages"""

    @pytest.fixture(scope="module")
    def package_cache(self):
        """Fixture to prepare package cache directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def get_installed_version(self, package_name):
        """Get the installed version of a package"""
        try:
            module = importlib.import_module(package_name)
            if hasattr(module, '__version__'):
                return module.__version__

            # Try using pkg_resources if __version__ attribute is not available
            return pkg_resources.get_distribution(package_name).version
        except (ImportError, pkg_resources.DistributionNotFound):
            return None

    def get_available_versions(self, package_name, limit=5):
        """Get available versions of a package from PyPI"""
        try:
            # Query PyPI JSON API
            url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # Get all version numbers and sort them
            versions = list(data["releases"].keys())
            # Sort versions (this is a simple sort, ideally would use packaging.version)
            versions.sort(reverse=True)

            return versions[:limit]  # Return only the most recent ones
        except Exception as e:
            pytest.skip(f"Could not fetch versions for {package_name}: {e}")
            return []

    def download_package(self, package_name, version, cache_dir):
        """Download a package from PyPI using pip"""
        download_dir = os.path.join(cache_dir, f"{package_name}-{version}")
        os.makedirs(download_dir, exist_ok=True)

        # Use pip to download the wheel
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "download",
                    "--no-deps",
                    "--only-binary=:all:",
                    "--dest",
                    download_dir,
                    f"{package_name}=={version}"
                ],
                check=True,
                capture_output=True
            )

            # Find the downloaded wheel
            wheel_files = [f for f in os.listdir(download_dir) if f.endswith('.whl')]
            if not wheel_files:
                pytest.skip(f"Could not find wheel for {package_name} {version}")
                return None

            wheel_path = os.path.join(download_dir, wheel_files[0])

            # Extract the wheel
            extract_path = os.path.join(download_dir, "extracted")
            os.makedirs(extract_path, exist_ok=True)

            with zipfile.ZipFile(wheel_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # Find the actual package directory
            for root, dirs, files in os.walk(extract_path):
                if os.path.basename(root) == package_name:
                    if '__init__.py' in files:
                        return root

            # If not found directly, look for .dist-info directory and search nearby
            for item in os.listdir(extract_path):
                if item.endswith('.dist-info'):
                    if os.path.exists(os.path.join(extract_path, package_name)):
                        return os.path.join(extract_path, package_name)

            pytest.skip(f"Could not locate package directory for {package_name} {version}")
            return None

        except subprocess.CalledProcessError as e:
            pytest.skip(f"Failed to download {package_name} {version}: {e.stderr.decode()}")
            return None

    def test_yaml_version_management(self, package_cache):
        """Test version management with PyYAML"""
        # Check if PyYAML is installed
        installed_version = self.get_installed_version('yaml')
        if not installed_version:
            pytest.skip("PyYAML is not installed, skipping test")

        print(f"Installed PyYAML version: {installed_version}")

        # Get available versions and select two different from installed
        available_versions = self.get_available_versions('pyyaml')
        test_versions = []

        for version in available_versions:
            if version != installed_version:
                test_versions.append(version)
                if len(test_versions) >= 2:
                    break

        if len(test_versions) < 1:
            pytest.skip("Could not find additional PyYAML versions to test")

        # Download the test versions
        version_paths = {}
        for version in test_versions:
            path = self.download_package('pyyaml', version, package_cache)
            if path:
                version_paths[version] = path

        if not version_paths:
            pytest.skip("Could not download any PyYAML versions")

        # Setup package manager with main and downloaded versions
        yaml_manager = setup_package_manager(
            name="yaml",
            register_main=True,
            versions=version_paths
        )

        # List versions
        versions = yaml_manager.list_versions()

        # Verify main version is registered
        assert any(v["is_main"] and v["version"] == installed_version for v in versions), \
            "Main PyYAML version not correctly registered"

        # Verify additional versions are registered
        for version in version_paths:
            assert any(v["version"] == version for v in versions), \
                f"Version {version} not registered correctly"

        # Test using each version
        for version in [installed_version] + list(version_paths.keys()):
            yaml_module = yaml_manager.use_version(version)
            assert hasattr(yaml_module, 'dump'), f"yaml.dump not available in version {version}"
            assert hasattr(yaml_module, 'safe_load'), f"yaml.safe_load not available in version {version}"

            # Test basic functionality
            test_data = {"key": "value", "numbers": [1, 2, 3]}
            yaml_str = yaml_module.dump(test_data)
            loaded_data = yaml_module.safe_load(yaml_str)
            assert loaded_data == test_data, f"Data not correctly processed with version {version}"

        # Test temporary version
        first_alt_version = list(version_paths.keys())[0]

        # Set main as active
        yaml_manager.use_version(installed_version)
        main_yaml = yaml_manager()

        with yaml_manager.temporary_version(first_alt_version) as temp_yaml:
            # Should temporarily use alternative version
            current = yaml_manager()
            assert current == temp_yaml
            assert yaml_manager.active_version == first_alt_version

        # Should switch back to main
        assert yaml_manager.active_version == installed_version
        assert yaml_manager() == main_yaml

    def test_requests_version_management(self, package_cache):
        """Test version management with requests"""
        # Check if requests is installed
        installed_version = self.get_installed_version('requests')
        if not installed_version:
            pytest.skip("requests is not installed, skipping test")

        print(f"Installed requests version: {installed_version}")

        # Get available versions and select one different from installed
        available_versions = self.get_available_versions('requests')
        test_versions = []

        for version in available_versions:
            if version != installed_version:
                test_versions.append(version)
                if len(test_versions) >= 1:
                    break

        if not test_versions:
            pytest.skip("Could not find additional requests versions to test")

        # Download test version
        version_paths = {}
        for version in test_versions:
            path = self.download_package('requests', version, package_cache)
            if path:
                version_paths[version] = path

        if not version_paths:
            pytest.skip("Could not download any requests versions")

        # Setup package manager with main and downloaded version
        requests_manager = setup_package_manager(
            name="requests",
            register_main=True,
            versions=version_paths
        )

        # Verify versions are registered
        versions = requests_manager.list_versions()
        assert any(v["is_main"] and v["version"] == installed_version for v in versions), \
            "Main requests version not correctly registered"

        for version in version_paths:
            assert any(v["version"] == version for v in versions), \
                f"Version {version} not registered correctly"

        # Test decorator
        alt_version = list(version_paths.keys())[0]
        with_alt_requests = create_decorator("requests", alt_version)

        @with_alt_requests
        def use_alt_requests():
            req = import_version("requests")
            return req

        # Run function with alternate version
        alt_requests = use_alt_requests()
        assert hasattr(alt_requests, 'get'), "get method missing from alternate requests"

        # Make sure it doesn't affect the manager's current state
        assert requests_manager.active_version != alt_version, \
            "Decorator changed the active version outside its scope"