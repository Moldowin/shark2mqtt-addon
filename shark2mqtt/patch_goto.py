"""Build-time patch: retry the Auth0 page load when Chromium reports ERR_NETWORK_CHANGED.

Upstream shark2mqtt 1.5.5 aborts the whole login if the first page load hits a
transient container network change. Fails the image build if the expected
upstream line is not found, so an upstream change cannot silently skip it.
"""
import sys
from pathlib import Path

path = Path(sys.argv[1])
src = path.read_text(encoding="utf-8")
needle = '                    await page.goto(authorize_url, wait_until="domcontentloaded")\n'
if src.count(needle) != 1:
    sys.exit(f"patch_goto: expected exactly one goto line in {path}, found {src.count(needle)}")
pad = " " * 20
replacement = (
    f"{pad}for _goto_try in range(6):\n"
    f"{pad}    try:\n"
    f"{pad}        await page.goto(authorize_url, wait_until=\"domcontentloaded\")\n"
    f"{pad}        break\n"
    f"{pad}    except Exception as _goto_err:\n"
    f"{pad}        if \"ERR_NETWORK_CHANGED\" not in str(_goto_err) or _goto_try == 5:\n"
    f"{pad}            raise\n"
    f"{pad}        logger.warning(\"Auth0 page load hit ERR_NETWORK_CHANGED; retrying in 3s (%d/5)\", _goto_try + 1)\n"
    f"{pad}        await asyncio.sleep(3)\n"
)
src = src.replace(needle, replacement)
compile(src, str(path), "exec")
path.write_text(src, encoding="utf-8")
print("patch_goto: applied")
