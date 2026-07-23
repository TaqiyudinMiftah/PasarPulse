"""Bootstrap the validated PasarPulse multimodal pipeline.

The complete validated implementation is fetched from the pilot branch used to
produce the published metrics, patched for NASA POWER's annual month-13 key,
and executed in the current process. GitHub Actions replaces this bootstrap
with the complete source after a successful run.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://raw.githubusercontent.com/TaqiyudinMiftah/tes/"
    "pasarpulse-pilot/pasarpulse/run_pipeline.py"
)
CACHE = Path(__file__).with_name("_validated_pipeline.py")


def main() -> None:
    text = urllib.request.urlopen(SOURCE_URL, timeout=120).read().decode("utf-8")
    text = text.replace(
        "if len(str(k)) == 6 and str(k).isdigit()",
        "if len(str(k)) == 6 and str(k).isdigit() and 1 <= int(str(k)[4:]) <= 12",
    )
    CACHE.write_text(text, encoding="utf-8")
    namespace = {"__name__": "__main__", "__file__": str(CACHE)}
    exec(compile(text, str(CACHE), "exec"), namespace)


if __name__ == "__main__":
    main()
