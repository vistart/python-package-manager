"""
Basic usage example for package_manager using PyYAML.

This example demonstrates:
1. Setting up a package manager for yaml
2. Using different versions
3. Switching between versions
"""
import os
import sys
import tempfile

from src.package_manager import setup_package_manager


def main():
    print("Package Manager Basic Usage Example with PyYAML")
    print("=" * 50)

    # Create a temporary directory for a custom PyYAML version
    custom_dir = tempfile.mkdtemp(prefix="custom_yaml_")

    # For demonstration purposes, we'll create a mock custom yaml version
    # In a real scenario, you'd have an actual different version installed here
    yaml_dir = os.path.join(custom_dir, "yaml")
    os.makedirs(yaml_dir, exist_ok=True)

    # Create a custom __init__.py with a different version
    with open(os.path.join(yaml_dir, "__init__.py"), "w") as f:
        f.write("""
# Custom PyYAML version for demonstration
__version__ = "custom-5.0.0"

# Import all from the real yaml for demonstration
import yaml as real_yaml
from yaml import *

# Override dump to demonstrate version difference
def dump(data, stream=None, **kwargs):
    if stream is None:
        return real_yaml.dump(data, stream, **kwargs) + "# Custom version output"
    result = real_yaml.dump(data, **kwargs)
    stream.write(result)
    stream.write("# Custom version output")
    return stream
""")

    # Setup package manager for yaml
    yaml_manager = setup_package_manager(
        name="yaml",
        register_main=True,  # Register the pip installed version
        versions={
            "custom": yaml_dir,  # Point to the yaml directory, not custom_dir
        }
    )

    # Print registered versions
    print("\nRegistered YAML versions:")
    for version_info in yaml_manager.list_versions():
        print(f"- {version_info['version']} {'(active)' if version_info.get('active') else ''}")
        print(f"  Path: {version_info['path']}")

    # Use the main version
    print("\nUsing main version:")
    yaml_main = yaml_manager.use_version(yaml_manager.active_version)
    data = {"example": "data", "list": [1, 2, 3]}
    print(f"YAML version: {getattr(yaml_main, '__version__', 'unknown')}")
    print("Dump result:")
    print(yaml_main.dump(data))

    # Switch to custom version
    print("\nSwitching to custom version:")
    yaml_custom = yaml_manager.use_version("custom")
    print(f"YAML version: {yaml_custom.__version__}")
    print("Dump result:")
    print(yaml_custom.dump(data))

    # Temporary use with context manager
    print("\nTemporarily using main version again:")
    with yaml_manager.temporary_version(yaml_manager.list_versions()[0]['version']) as yaml_temp:
        print(f"YAML version in context: {getattr(yaml_temp, '__version__', 'unknown')}")
        print("Dump result:")
        print(yaml_temp.dump(data))

    # After context, should be back to custom
    print("\nAfter context, back to previous version:")
    yaml_current = yaml_manager()
    print(f"YAML version: {yaml_current.__version__}")

    # Clean up
    print("\nCleaning up temporary directory...")
    import shutil
    shutil.rmtree(custom_dir)
    print("Done!")


if __name__ == "__main__":
    # Check if PyYAML is installed
    try:
        import yaml

        main()
    except ImportError:
        print("Error: This example requires PyYAML to be installed.")
        print("Please install it using: pip install pyyaml")
        sys.exit(1)