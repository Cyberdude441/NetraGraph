"""Runtime guard for the pinned scientific ML stack."""
from __future__ import annotations

import sys

SUPPORTED_MESSAGE = (
    "NetraGraph ML requires Python 3.11 or 3.12.\n"
    "Python 3.14 is currently not supported for the pinned scientific ML stack."
)


def ensure_supported_ml_runtime() -> None:
    if sys.version_info[:2] not in {(3, 11), (3, 12)}:
        print(SUPPORTED_MESSAGE, file=sys.stderr)
        raise RuntimeError(SUPPORTED_MESSAGE)
