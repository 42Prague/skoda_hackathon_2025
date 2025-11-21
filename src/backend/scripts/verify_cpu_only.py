#!/usr/bin/env python3
"""
Fail fast if any GPU or CUDA-specific packages are installed in the environment.
"""

from __future__ import annotations

import pkgutil
import sys


def main() -> None:
    gpu_packages = [
        module.name
        for module in pkgutil.iter_modules()
        if module.name.startswith("nvidia")
        or "cuda" in module.name
        or "cudnn" in module.name
        or "cublas" in module.name
    ]
    if gpu_packages:
        raise SystemExit(f"GPU packages detected: {gpu_packages}")
    print("CPU-only environment verified.")


if __name__ == "__main__":
    main()

