from __future__ import absolute_import

from setuptools import setup

setup(
    name="Socks5man",
    version="0.3.0",
    author="Ricardo van Zutphen",
    author_email="ricardo@hatching.io",
    packages=[
        "socks5man",
    ],
    keywords="socks5man socks5 tester management library verification",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Monitoring",
        "Topic :: Security",
    ],
    license="GPLv3",
    description="SOCKS5 server management tool and library",
    long_description=open("README.md", "r").read(),
    include_package_data=True,
    url="https://github.com/RicoVZ/socks5man",
    install_requires=[r.strip() for r in open("requirements.txt", "r").readlines()],
    python_requires=">=3.6",
    extras_require={
        ":sys_platform == 'win32'": [
            "win-inet-pton==1.0.1",
        ],
    },
    tests_require=[
        "pytest",
        "mock"
    ],
    entry_points={
        "console_scripts": [
            "socks5man = socks5man.main:main"
        ],
    }
)
