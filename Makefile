
---

# 4️⃣ Prep for PyPI release

## ✅ `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "simple-auditlog"
version = "0.1.0"
description = "Lightweight audit logging for Django with admin diffs"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
  {name = "Your Name"}
]
keywords = ["django", "audit", "logging", "admin"]
classifiers = [
  "Framework :: Django",
  "Framework :: Django :: 4.2",
  "Programming Language :: Python :: 3",
  "License :: OSI Approved :: MIT License",
]

dependencies = [
  "Django>=3.2",
  "asgiref>=3.6",
]

[project.urls]
Homepage = "https://github.com/yourname/simple-auditlog"
