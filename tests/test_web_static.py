"""Static-page checks for regression to a fabricated backend report."""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_standalone_demo_is_explicitly_unsigned():
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    assert "LOCAL_UNSIGNED_DEMO" in html
    assert "HMAC_SHA256_e83" not in html
    assert "fetch('/api/audit'" not in html
    assert 'id="audit-form"' in html
    assert 'id="export"' in html


def test_browser_javascript_parses(tmp_path):
    if shutil.which("node") is None:
        pytest.skip("Node.js not installed")
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    source = html.split("<script>", 1)[1].split("</script>", 1)[0]
    script = tmp_path / "web-demo.js"
    script.write_text(source, encoding="utf-8")
    result = subprocess.run(["node", "--check", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
