"""
Sphinx configuration for the Module_4 documentation.
"""

import os
import sys

# Ensure the ``src/`` directory is on the path so ``autodoc`` can
# import the application modules.
sys.path.insert(0, os.path.abspath("../../src"))

# In order to import ``app.py`` without requiring a real ``libpq``
# library, we inject a fake ``psycopg`` module into ``sys.modules``
# before Sphinx tries to import the real one.
from unittest.mock import MagicMock


class FakePsycopg:
    """A stand-in for the ``psycopg`` module that raises on any call."""
    def __getattr__(self, name):
        if name in ("connect", "Error", "DatabaseError"):
            return MagicMock()
        raise AttributeError(name)


sys.modules["psycopg"] = FakePsycopg()

# ------------------------------------------------------------------
# Project information
# ------------------------------------------------------------------
project = "GradCafe Applicant Analysis"
author = "JHU Software Concepts — Module 4"
release = "1.0.0"
copyright = "2026, JHU Software Concepts"

# ------------------------------------------------------------------
# General Sphinx configuration
# ------------------------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",       # auto-generate API docs from docstrings
    "sphinx.ext.napoleon",      # support Google/NumPy-style docstrings
    "sphinx.ext.viewcode",      # link to annotated source code
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

# ------------------------------------------------------------------
# HTML output options
# ------------------------------------------------------------------
html_theme = "alabaster"
html_static_path = ["_static"]