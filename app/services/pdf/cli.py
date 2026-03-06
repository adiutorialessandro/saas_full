from __future__ import annotations

import json
import sys
from pathlib import Path

from .engine import generate_report


def main() -> int:
    if len(sys.argv) < 4:
        print("Usage: python -m app.services.pdf.cli <template> <payload.json> <out.pdf>")
        print("Templates: saas_scan_v1 | one_pager_v1")
        return 1

    template = sys.argv[1]
    payload_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3])

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    scan_meta = payload.get("scan_meta") or {}
    vm = payload.get("vm") or {}

    generate_report(out_path, scan_meta, vm, template=template)
    print(f"OK -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
