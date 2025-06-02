#!/usr/bin/env python
"""
Setup script for DumpSleuth
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
requirements_file = this_directory / "requirements" / "base.txt"
if requirements_file.exists():
    requirements = requirements_file.read_text().splitlines()

setup(
    name="dumpsleuth",
    version="2.0.0",
    author="James Nelson",
    author_email="james.nelson@jamesnelsonsec.xyz",
    description="Modern Memory Dump Analysis Toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OVHGERMANY/DumpSleuth",
    project_urls={
        "Bug Tracker": "https://github.com/OVHGERMANY/DumpSleuth/issues",
        "Documentation": "https://github.com/OVHGERMANY/DumpSleuth/wiki",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7",
    install_requires=[
        "click>=8.0.0",
        "rich>=10.0.0",
        "pyyaml>=5.4",
        "python-magic-bin>=0.4.14;platform_system=='Windows'",
        "python-magic>=0.4.24;platform_system!='Windows'",
        "hexdump>=3.3",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.910",
            "sphinx>=4.0",
        ],
        "web": [
            "fastapi>=0.68",
            "uvicorn>=0.15",
            "jinja2>=3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dumpsleuth=dumpsleuth.ui.cli:cli",
            "ds=dumpsleuth.ui.cli:cli",  # Short alias
        ],
    },
    include_package_data=True,
    package_data={
        "dumpsleuth": [
            "config/*.yaml",
            "templates/*.html",
            "templates/*.css",
            "templates/*.js",
        ],
    },
)