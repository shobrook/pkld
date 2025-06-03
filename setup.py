import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup
from codecs import open

if sys.version_info[:3] < (3, 0, 0):
    print("Requires Python 3 to run.")
    sys.exit(1)

with open("README.md", encoding="utf-8") as file:
    readme = file.read()

setup(
    name="pkld",
    description="Persistent caching for Python functions",
    long_description=readme,
    long_description_content_type="text/markdown",
    version="v1.2.0",
    packages=find_packages(),
    python_requires=">=3",
    url="https://github.com/shobrook/pkld",
    author="shobrook",
    author_email="shobrookj@gmail.com",
    # classifiers=[],
    install_requires=["filelock"],
    requires=["filelock"],
    keywords=[],
    license="MIT",
)
