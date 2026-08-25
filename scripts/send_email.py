"""Send the generated HTML report via SMTP as a beautiful inline-image email.

Reads ``reports/email_report.html`` (produced by ``build_email.py``), attaches
the figures referenced via ``cid:`` as inline images, and sends through an SMTP
server. Credentials are supplied via environment variables (in CI, GitHub
secrets) so nothing sensitive lives in the repo.

Environment variables
----------------------
  SMTP_HOST      e.g. smtp.gmail.com
  SMTP_PORT      e.g. 587 (STARTTLS) — default 587
  SMTP_USER      login username
  SMTP_PASS      login password / app password
  EMAIL_FROM     sender address
  EMAIL_TO       comma-separated recipient(s)
  EMAIL_SUBJECT  optional
  REPORT_HTML    optional override path

Use ``--dry-run`` to validate configuration and render without sending.
"""

from __future__ import annotations

import argparse
import os
import re
import smtplib
import sys
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src.config as cfg

FIG_DIR = cfg.REPORTS_DIR / "figures"
DEFAULT_HTML = cfg.REPORTS_DIR / "email_report.html"


def _required(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise SystemExit(f"Missing required environment variable: {name}")
    return val


def _collect_figures(html: str) -> list[tuple[str, Path]]:
    """Return (cid, path) pairs for every cid: referenced in the HTML."""
    cids = re.findall(r'src="cid:([^"]+)"', html)
    found: list[tuple[str, Path]] = []
    for cid in dict.fromkeys(cids):  # preserve order, dedupe
        candidate = FIG_DIR / f"{cid}.png"
        if candidate.exists():
            found.append((cid, candidate))
    return found


def build_message(html_path: Path, subject: str, sender: str, recipients: list[str]) -> MIMEMultipart:
    html = html_path.read_text()
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText("Your daily Employee Exit Survey report is attached as HTML.", "plain"))
    alt.attach(MIMEText(html, "html"))
    msg.attach(alt)

    for cid, path in _collect_figures(html):
        with path.open("rb") as fh:
            img = MIMEImage(fh.read(), name=f"{cid}.png")
        img.add_header("Content-ID", f"<{cid}>")
        img.add_header("Content-Disposition", "inline", filename=f"{cid}.png")
        msg.attach(img)
    return msg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Validate config and render without sending")
    args = ap.parse_args()

    host = _required("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = _required("SMTP_USER")
    password = _required("SMTP_PASS")
    sender = _required("EMAIL_FROM")
    recipients = [r.strip() for r in _required("EMAIL_TO").split(",") if r.strip()]
    subject = os.environ.get("EMAIL_SUBJECT", "Daily Employee Exit Survey Report")
    html_path = Path(os.environ.get("REPORT_HTML", str(DEFAULT_HTML)))

    if not html_path.exists():
        raise SystemExit(f"HTML report not found: {html_path}. Run build_email.py first.")

    msg = build_message(html_path, subject, sender, recipients)
    figs = _collect_figures(html_path.read_text())

    if args.dry_run:
        print(f"[dry-run] host={host}:{port} user={user} from={sender} to={recipients}")
        print(f"[dry-run] subject={subject!r} html={html_path} figures={[f for f, _ in figs]}")
        return

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(sender, recipients, msg.as_string())
    print(f"Sent report to {recipients} ({len(figs)} inline figures).")


if __name__ == "__main__":
    main()
