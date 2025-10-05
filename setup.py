"""
Setup script for Claude Code Agent.
"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="codegenie",
    version="0.1.0",
    author="Sherin Joseph Roy",
    author_email="sherin.joseph2217@gmail.com",
    description="CodeGenie - A local AI coding agent powered by Ollama",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sherin-SEF-AI/code-genie",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "codegenie=codegenie.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
