#!/usr/bin/env python
"""Script to check if all required dependencies are installed."""

import sys
import importlib.util
import pkg_resources
import subprocess
from pathlib import Path

# List of required packages for the project
REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "chromadb",
    "langchain",
    "openai",
    "tqdm",
    "PyMuPDF",
    "python-docx",
    "tiktoken",
    "grpcio",
    "protobuf",
]


def check_package(package_name):
    """Check if a package is installed and usable."""
    try:
        # Try to import the package
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            print(f"❌ {package_name} is not importable")
            return False

        # Try to get the package version
        version = pkg_resources.get_distribution(package_name).version
        print(f"✅ {package_name} {version} is installed and importable")
        return True
    except (ModuleNotFoundError, pkg_resources.DistributionNotFound):
        print(f"❌ {package_name} is not installed or importable")
        return False
    except Exception as e:
        print(f"❌ {package_name} raised an error during import: {str(e)}")
        return False


def main():
    """Check all required dependencies and print summary."""
    print("Checking dependencies...")
    print("-" * 50)

    # Check Python version
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")

    # Check all packages
    missing_packages = []
    for package in REQUIRED_PACKAGES:
        if not check_package(package):
            missing_packages.append(package)

    # Summary
    print("-" * 50)
    if missing_packages:
        print(
            f"❌ {len(missing_packages)} packages are missing or not importable: {', '.join(missing_packages)}"
        )
        print("\nRecommendation: Try reinstalling dependencies:")
        print("  make pip-install")
        return 1
    else:
        print(
            f"✅ All {len(REQUIRED_PACKAGES)} required packages are installed and importable!"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
