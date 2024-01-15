import setuptools

from unipile_integration import __version__, __email__, __author__

with open('requirements.txt') as f:
    requirements = f.read().splitlines()


setuptools.setup(
    name="unipile_integration",
    version=__version__,
    author=__author__,
    author_email=__email__,
    description="Python package to add integration with unipile",
    packages=setuptools.find_packages(),
    package_dir={"unipile_integration": "./unipile_integration"},
    install_requires=requirements,
)
