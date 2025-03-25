"""
Exception classes for the package manager
"""


class PackageManagerError(Exception):
    """Base exception for all package manager errors"""
    pass


class PackageNotFoundError(PackageManagerError):
    """Raised when a package cannot be found"""
    def __init__(self, package_name):
        self.package_name = package_name
        super().__init__(f"Package not found: {package_name}")


class VersionNotFoundError(PackageManagerError):
    """Raised when a specific version cannot be found"""
    def __init__(self, package_name, version):
        self.package_name = package_name
        self.version = version
        super().__init__(f"Version {version} not found for package {package_name}")


class ImportError(PackageManagerError):
    """Raised when a package cannot be imported"""
    pass


class ConfigError(PackageManagerError):
    """Raised when there's an error in the configuration"""
    pass