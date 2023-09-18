from setuptools import find_packages
from distutils.core import setup

from hugchat_api import __version__, __description__, __email__, __url__, __author__

setup(
    name="hugchat_api",
    version=__version__,
    author=__author__,
    author_email=__email__,
    description=__description__,
    url=__url__,
    project_urls = {
        "Wiki": "https://github.com/ogios/huggingchat-api/wiki",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    exclude_package_data={
        "json": [
            "usercookies",
            "*.json"
        ],
        "others": [
            "__pycache__",
            ".git",
            ".github"
        ]
    },
    install_requires=[
        "urllib3",
        "aiohttp",
        "dataclasses-json",
    ],
    license="GNU General Public License v3.0",
    long_description=open("./README.md", "r").read(),
    long_description_content_type='text/markdown',
)
