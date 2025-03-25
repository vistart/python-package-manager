"""
Pytest configuration for package_manager tests.
"""
import os
import sys

# Add the src directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))