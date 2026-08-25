"""Build a beautifully styled HTML email from the markdown insights report.

Reads ``reports/business_insights.md`` and produces
``reports/email_report.html``:

  * converts the Markdown to HTML (tables, fenced code)
  * rewrites the embedded figure links to inline ``cid:`` references so the
    companion ``send_email.py`` can attach them as inline images
  * wraps everything in a responsive, on-brand HTML template

Run ``python scripts/build_email.py`` (optionally ``--out path.html``).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import markdown

import src.config as cfg

FIG_DIR = cfg.REPORTS_DIR / "figures"
DEFAULT_OUT = cfg.REPORTS_DIR / "email_report.html"

# Brand palette (matches visualize.PALETTE / README).
DETE_BLUE = "#2c7fb8"
TAFE_ORANGE = "#d95f0e"
INK = "#1f2d3d"
MUTED = "#5b6b7b"


def _rewrite_figures(md_text: str) -> tuple[str, list[str]]:
    """Replace Markdown image links with cid references; return (text, cids)."""
    cids: list[str] = []

    def _repl(match: re.Match) -> str:
        alt = match.group(1)
        rel = match.group(2)
        cid = Path(rel).stem
        cids.append(cid)
        return (
            f'<img src="cid:{cid}" alt="{alt}" '
            f'style="max-width:100%;height:auto;border-radius:10px;'
            f'margin:14px 0;box-shadow:0 1px 4px rgba(0,0,0,.12)" />'
        )

    # Match markdown images: ![alt](path)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _repl, md_text)
    return text, cids


def _brand_template(body_html: str, generated_at: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Employee Exit Survey Report</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:{INK};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="680" cellpadding="0" cellspacing="0" style="width:680px;max-width:92%;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 4px 18px rgba(0,0,0,.08);">
          <tr>
            <td style="background:linear-gradient(90deg,{DETE_BLUE},{TAFE_ORANGE});padding:26px 32px;color:#ffffff;">
              <div style="font-size:22px;font-weight:700;letter-spacing:.2px;">Employee Exit Survey Analytics</div>
              <div style="font-size:13px;opacity:.92;margin-top:4px;">Automated daily exit-survey intelligence &mdash; DETE &amp; TAFE</div>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 32px 8px;">
              {body_html}
            </td>
          </tr>
          <tr>
            <td style="padding:10px 32px 28px;">
              <div style="border-top:1px solid #e6eaee;padding-top:14px;font-size:12px;color:{MUTED};">
                Generated automatically on {generated_at}. This report is produced by the
                <em>employee-exit-survey-analytics</em> pipeline. Figures are embedded inline.
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def build(md_path=None, out_path=None) -> Path:
    md_path = Path(md_path or cfg.REPORTS_DIR / "business_insights.md")
    out_path = Path(out_path or DEFAULT_OUT)
    if not md_path.exists():
        raise FileNotFoundError(f"Report not found: {md_path}. Run the pipeline first.")

    md_text = md_path.read_text()
    body_md, _ = _rewrite_figures(md_text)
    body_html = markdown.markdown(body_md, extensions=["tables", "fenced_code"])

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    html = _brand_template(body_html, generated_at)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=None, help="Path to the markdown report")
    ap.add_argument("--out", default=None, help="Path to write the HTML email")
    args = ap.parse_args()
    out = build(args.md, args.out)
    print(f"Wrote HTML email -> {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
