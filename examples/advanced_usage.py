"""
Advanced usage example for package_manager using PyYAML.

This example demonstrates:
1. Dynamic version discovery and registration
2. Using decorators for version-specific functions
3. Working with metadata
4. Error handling
"""
import os
import sys
import tempfile
import logging

from src.package_manager import get_package_manager, import_version, create_decorator
from src.package_manager.exceptions import VersionNotFoundError

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("package_manager")

def create_yaml_versions(base_dir, versions):
    """
    Create multiple mock YAML versions for demonstration

    Args:
        base_dir: Base directory to create versions in
        versions: List of version strings to create

    Returns:
        Dictionary mapping version names to their paths
    """
    version_paths = {}

    for version in versions:
        # Create directory for this version
        version_dir = os.path.join(base_dir, f"yaml-{version}")
        yaml_dir = os.path.join(version_dir, "yaml")
        os.makedirs(yaml_dir, exist_ok=True)

        print(f"Created directory: {yaml_dir}")

        # Create __init__.py with custom version and behavior
        init_file = os.path.join(yaml_dir, "__init__.py")
        with open(init_file, "w") as f:
            f.write(f"""
# Mock PyYAML version {version} for demonstration
__version__ = "{version}"

# Import actual yaml functionality
import yaml as real_yaml
from yaml import *

# Override dump to demonstrate version difference
def dump(data, stream=None, **kwargs):
    if stream is None:
        result = real_yaml.dump(data, stream, **kwargs)
        return result + f"# Version {version} output"
    result = real_yaml.dump(data, **kwargs)
    stream.write(result)
    stream.write(f"# Version {version} output")
    return stream

# Add version-specific functionality
def get_version_info():
    return {{
        "version": "{version}",
        "is_mock": True,
        "capabilities": ["basic", "custom-{version}"]
    }}
""")
        print(f"Created __init__.py at: {init_file}")
        # Verify file exists
        if os.path.exists(init_file):
            print(f"Verified __init__.py exists at: {init_file}")
        else:
            print(f"ERROR: Failed to create __init__.py at: {init_file}")

        # Register yaml directory, this is the key fix
        version_paths[version] = yaml_dir
        print(f"Registered version {version} at path: {yaml_dir}")
        print(f"Directory contents: {os.listdir(yaml_dir)}")

    return version_paths


def main():
    print("Package Manager Advanced Usage Example with PyYAML")
    print("=" * 60)

    # Create temporary directory structure with multiple versions
    temp_base = tempfile.mkdtemp(prefix="yaml_versions_")
    print(f"Created temporary directory: {temp_base}")

    versions = ["5.0.0", "6.0.2", "legacy"]
    version_paths = create_yaml_versions(temp_base, versions)

    # Get package manager for yaml
    yaml_manager = get_package_manager("yaml")

    # Register main version if available
    print("\nRegistering main version...")
    main_version = yaml_manager.register_main_version()
    if main_version:
        print(f"Main version registered: {main_version.version}")
    else:
        print("Main version not found (PyYAML not installed)")

    # Dynamic version discovery and registration with metadata
    print("\nDynamically discovering and registering versions...")
    for version, path in version_paths.items():
        try:
            # Verify path exists and contents
            print(f"Verifying path for {version}: {path}")
            print(f"Path exists: {os.path.exists(path)}")
            print(f"Path is directory: {os.path.isdir(path)}")
            if os.path.exists(path):
                print(f"Directory contents: {os.listdir(path)}")
                init_file = os.path.join(path, "__init__.py")
                print(f"__init__.py exists: {os.path.exists(init_file)}")

            metadata = {
                "source": "mock",
                "created_at": "2025-03-25",
                "purpose": "demonstration"
            }
            pkg_ver = yaml_manager.register_version(version, path, metadata=metadata)
            print(f"Registered version {version} at {path}")
        except ValueError as e:
            print(f"Failed to register {version}: {e}")

    # List all versions with details
    print("\nDetailed version listing:")
    print("-" * 40)
    for info in yaml_manager.list_versions():
        print(f"Version: {info['version']} {'(active)' if info['active'] else ''}")
        print(f"  Path: {info['path']}")
        print(f"  Main: {'Yes' if info['is_main'] else 'No'}")
        if "metadata" in info and info["metadata"]:
            print("  Metadata:")
            for key, value in info["metadata"].items():
                print(f"    {key}: {value}")
        print("-" * 40)

    # Create decorators for specific versions
    print("\nCreating version-specific decorators...")

    # Find a version that exists to create a decorator
    available_versions = [v['version'] for v in yaml_manager.list_versions()]
    decorator_version = available_versions[0] if available_versions else None

    if decorator_version:
        with_specific_yaml = create_decorator("yaml", decorator_version)

        @with_specific_yaml
        def process_document(data):
            """Process a document with a specific YAML version"""
            yaml_module = import_version("yaml")  # Will use the version from decorator
            print(f"Processing with YAML version: {yaml_module.__version__}")
            return yaml_module.dump(data)

        # Test the decorated function
        print("\nUsing decorated function (should use version from decorator):")
        test_data = {"name": "Test", "values": [1, 2, 3]}
        result = process_document(test_data)
        print(result)
    else:
        print("No versions available for decorator demonstration")

    # Error handling demonstration
    print("\nError handling demonstration:")
    try:
        # Try to use a non-existent version
        yaml_manager.use_version("non-existent-version")
    except VersionNotFoundError as e:
        print(f"Expected error: {e}")

    # Switch between versions
    if len(available_versions) >= 2:
        print("\nSwitching between versions:")

        # Use first version
        ver1 = available_versions[0]

        # Detailed logging of first version loading process
        print(f"Loading first version: {ver1}")
        print(f"Version path: {yaml_manager.versions[ver1].path}")
        print(f"Path exists: {os.path.exists(yaml_manager.versions[ver1].path)}")
        if os.path.exists(yaml_manager.versions[ver1].path):
            print(f"Directory contents: {os.listdir(yaml_manager.versions[ver1].path)}")

        yaml1 = yaml_manager.use_version(ver1)
        print(f"Using {ver1}:")
        print(yaml1.dump({"test": "data"}))

        # Use second version
        ver2 = available_versions[1]

        # Detailed logging of second version loading process
        print(f"Loading second version: {ver2}")
        print(f"Version path: {yaml_manager.versions[ver2].path}")
        print(f"Path exists: {os.path.exists(yaml_manager.versions[ver2].path)}")
        if os.path.exists(yaml_manager.versions[ver2].path):
            print(f"Directory contents: {os.listdir(yaml_manager.versions[ver2].path)}")
            init_file = os.path.join(yaml_manager.versions[ver2].path, "__init__.py")
            print(f"__init__.py exists: {os.path.exists(init_file)}")

        yaml2 = yaml_manager.use_version(ver2)
        print(f"\nUsing {ver2}:")
        print(yaml2.dump({"test": "data"}))

        # Version-specific functionality
        if hasattr(yaml2, "get_version_info"):
            print("\nVersion-specific functionality:")
            print(yaml2.get_version_info())

    # Clean up
    print("\nCleaning up temporary directories...")
    import shutil
    shutil.rmtree(temp_base)
    print("Done!")


if __name__ == "__main__":
    # Check if PyYAML is installed
    try:
        import yaml

        main()
    except ImportError:
        print("This example works best with PyYAML installed, but will demonstrate")
        print("mock versions even without it.")
        main()