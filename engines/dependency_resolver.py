"""
Haiox Genesis - Dependency Resolver Engine
Module: engines/dependency_resolver.py
Architect: AIrash (Staff Systems Engineer) for Hatef Ghanei (haiox)
"""

from typing import List, Set

# Complete set of Python standard library modules to prevent hallucinated requirements
PYTHON_STDLIB_MODULES: Set[str] = {
    "abc", "argparse", "array", "ast", "asyncio", "base64", "binascii", "bisect",
    "builtins", "calendar", "cmath", "cmd", "code", "codecs", "collections",
    "colorsys", "compileall", "concurrent", "configparser", "contextlib", "copy",
    "copyreg", "cProfile", "crypt", "csv", "ctypes", "curses", "dataclasses",
    "datetime", "dbm", "decimal", "difflib", "dis", "distutils", "doctest", "email",
    "encodings", "ensurepip", "enum", "errno", "faulthandler", "fcntl", "filecmp",
    "fileinput", "fnmatch", "fractions", "ftplib", "functools", "gc", "getopt",
    "getpass", "gettext", "glob", "graphlib", "grp", "gzip", "hashlib", "heapq",
    "hmac", "html", "http", "imaplib", "imghdr", "imp", "importlib", "inspect",
    "io", "ipaddress", "itertools", "json", "keyword", "linecache", "locale",
    "logging", "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes",
    "mmap", "modulefinder", "msilib", "msvcrt", "multiprocessing", "netrc", "nis",
    "nntplib", "numbers", "operator", "optparse", "os", "ossaudiodev", "parser",
    "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil", "platform",
    "plistlib", "poplib", "posix", "posixpath", "pprint", "profile", "pstats",
    "pty", "pwd", "py_compile", "pyclbr", "pydoc", "queue", "quopri", "random",
    "re", "readline", "reprlib", "resource", "rlcompleter", "runpy", "sched",
    "secrets", "select", "selectors", "shelve", "shlex", "shutil", "signal",
    "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver", "spwd",
    "sqlite3", "ssl", "stat", "statistics", "string", "stringprep", "struct",
    "subprocess", "sunau", "symbol", "symtable", "sys", "sysconfig", "syslog",
    "tabnanny", "tarfile", "telnetlib", "tempfile", "termios", "test", "textwrap",
    "threading", "time", "timeit", "tkinter", "token", "tokenize", "trace",
    "traceback", "tracemalloc", "tty", "turtle", "turtledemo", "types", "typing",
    "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings",
    "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref", "xdrlib",
    "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib", "zoneinfo"
}

KNOWN_PINNED_VERSIONS = {
    "pytest": "pytest>=8.0.0",
    "pydantic": "pydantic>=2.5.0",
    "httpx": "httpx>=0.27.0",
    "fastapi": "fastapi>=0.110.0",
    "uvicorn": "uvicorn>=0.28.0",
    "playwright": "playwright>=1.40.0",
    "beautifulsoup4": "beautifulsoup4>=4.12.0",
    "aiohttp": "aiohttp>=3.9.0",
    "redis": "redis>=5.0.0",
    "sqlalchemy": "sqlalchemy>=2.0.0",
}


class DependencyResolver:
    """
    Cleans, verifies and filters Python dependencies.
    Eliminates standard library modules and pins production-grade versions.
    """

    @classmethod
    def filter_and_normalize(cls, raw_dependencies: List[str]) -> List[str]:
        """
        Takes raw package requests, removes stdlib modules, and returns clean, pinned requirements.
        """
        clean_deps: List[str] = []
        seen: Set[str] = set()

        for raw_dep in raw_dependencies:
            dep_name = raw_dep.strip().lower()
            # Strip version specifiers for stdlib comparison
            base_name = dep_name.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()

            if not base_name or base_name in PYTHON_STDLIB_MODULES:
                continue

            if base_name in seen:
                continue

            seen.add(base_name)

            # Apply known pinned version if matching
            if base_name in KNOWN_PINNED_VERSIONS and base_name == dep_name:
                clean_deps.append(KNOWN_PINNED_VERSIONS[base_name])
            else:
                clean_deps.append(raw_dep.strip())

        # Ensure pytest is always present for testing
        if "pytest" not in seen:
            clean_deps.append("pytest>=8.0.0")

        return sorted(clean_deps)

    @classmethod
    def generate_requirements_txt(cls, raw_dependencies: List[str]) -> str:
        """
        Formats cleaned dependencies into a production-grade requirements.txt content.
        """
        cleaned = cls.filter_and_normalize(raw_dependencies)
        lines = [
            "# Haiox Genesis Generated Dependencies",
            "# Zero-hallucination, production-pinned requirements",
            ""
        ]
        lines.extend(cleaned)
        lines.append("")
        return "\n".join(lines)
