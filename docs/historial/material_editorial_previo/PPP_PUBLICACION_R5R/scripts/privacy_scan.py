#!/usr/bin/env python3
"""Heuristic local scan of text files; not a security guarantee."""
import argparse
import os
import re
from pathlib import Path

PATTERNS = {
    "ruta_home": re.compile(r"(?:/home/[^/\s]+|/Users/[^/\s]+|C:\\Users\\[^\\\s]+)"),
    "clave_privada": re.compile(r"-----BEGIN (?:OPENSSH|RSA|EC|DSA|PRIVATE) (?:PRIVATE )?KEY-----"),
    "token_gh": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    "token_api": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    "correo": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}
SKIP = {".git", "__pycache__", ".venv", "venv"}
SUFFIX = {".md", ".txt", ".py", ".json", ".jsonl", ".csv", ".yaml", ".yml", ".toml", ".sh", ".html", ".js", ".css", ".gitignore"}

def scan(root):
    hits = 0
    paths = [root] if root.is_file() else (p for p in root.rglob("*") if p.is_file())
    for path in paths:
        if path.name == "privacy_scan.py" or any(part in SKIP for part in path.parts) or (path.suffix.lower() not in SUFFIX and path.name != ".gitignore"):
            continue
        if path.stat().st_size > 2_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        for line_no, line in enumerate(content.splitlines(), 1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    print(f"REVISAR {path}:{line_no} [{label}]")
                    hits += 1
    print(f"Coincidencias a revisar: {hits}. Escaneo heurístico, NO certificación.")
    return 1 if hits else 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".")
    args = parser.parse_args()
    raise SystemExit(scan(Path(args.path)))
