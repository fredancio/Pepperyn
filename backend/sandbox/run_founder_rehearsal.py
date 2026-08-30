from __future__ import annotations

import json
import sys

from sandbox.synthetic_product import run_rehearsal
from sandbox.synthetic_product import SandboxRefused


if __name__ == "__main__":
    try:
        result = run_rehearsal()
    except SandboxRefused as exc:
        print(f"Sandbox stopped safely: {exc}", file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2, default=dict))
