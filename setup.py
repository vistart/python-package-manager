"""
Setup script for package_manager
"""
import codecs
import os
import re

import setuptools

def read(rel_path):
    """Read file."""
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r', 'utf-8') as fp:
        return fp.read()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

def find_version(rel_path):
    """Get version from __init__.py file."""
    init_file = read(rel_path)
    pattern = r'^__version__\s*=\s*"((?:[1-9]\d*!)?\d+(?:\.\d+)*(?:[-._]?(?:a|alpha|b|beta|rc|pre|preview)(?:[-._]?\d+)?)?(?:\.post(?:0|[1-9]\d*))?(?:\.dev(?:0|[1-9]\d*))?(?:\+[a-z0-9]+(?:[._-][a-z0-9]+)*)?)"$'
    version_match = re.search(pattern, init_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setuptools.setup(
    name="package_manager",
    version=find_version("src/__init__.py"),
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.8",
)