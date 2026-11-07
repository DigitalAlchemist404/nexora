#!/usr/bin/env python3
"""Entrada a la beta de NEXORA (Linux, macOS y Windows)."""
import sys
if sys.version_info < (3, 9):
    sys.exit('NEXORA necesita Python 3.9 o más reciente. Versión actual: ' + sys.version.split()[0])
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(errors='replace')  # consolas de Windows sin UTF-8: no romper por tildes o flechas
    except (AttributeError, ValueError):
        pass
from pieza_por_pieza.cli import main
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nHasta luego. (Ctrl+C)')
