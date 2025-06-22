#!/usr/bin/env python3
"""
Setup script for ktra - Personal AI Agent
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ktra",
    version="1.0.0",
    author="ktra Development Team",
    author_email="",
    description="Personal AI Agent using OpenAI Agent SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/ktra",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "ktra": [
            "prompts/*.txt",
            "memory/*.json",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Office/Business",
        "Topic :: Utilities",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ktra=ktra.cli:main_cli",
        ],
    },
    keywords="ai, agent, task-management, cli, openai",
    project_urls={
        "Bug Reports": "https://github.com/your-username/ktra/issues",
        "Source": "https://github.com/your-username/ktra",
    },
)