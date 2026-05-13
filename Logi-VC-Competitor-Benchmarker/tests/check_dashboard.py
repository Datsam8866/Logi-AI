import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from generate_dashboard import build_html, load_devices


def main():
    server_source = (BASE / "serve_dashboard.py").read_text(encoding="utf-8-sig")
    if "from generate_dashboard import load_devices, build_html" in server_source:
        raise SystemExit("Server refresh caches dashboard generator functions; reload generate_dashboard on each refresh")

    html = build_html(load_devices())

    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
    if not scripts:
        raise SystemExit("No inline dashboard scripts found")

    for index, script in enumerate(scripts, start=1):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(script)
            script_path = f.name
        try:
            result = subprocess.run(
                ["node", "--check", script_path],
                cwd=BASE,
                text=True,
                encoding="utf-8",
                capture_output=True,
            )
        finally:
            os.unlink(script_path)
        if result.returncode != 0:
            raise SystemExit(f"Inline script {index} has invalid JavaScript:\n{result.stderr}")

    invalid_teardown_hrefs = re.findall(r'href="(N/A[^"]*)"', html)
    if invalid_teardown_hrefs:
        raise SystemExit("Invalid teardown links rendered: " + ", ".join(invalid_teardown_hrefs))

    print("Dashboard checks passed")


if __name__ == "__main__":
    main()
