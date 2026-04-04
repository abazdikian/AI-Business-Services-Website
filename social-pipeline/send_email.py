"""
Send an HTML email via Gmail API.
"""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import ALICE_EMAIL
from gmail_auth import get_gmail_service


def send_email(subject, html_body):
    """Send an HTML email to Alice via Gmail API."""
    service = get_gmail_service()

    msg = MIMEMultipart("alternative")
    msg["to"] = ALICE_EMAIL
    msg["from"] = ALICE_EMAIL
    msg["subject"] = subject

    # Plain text fallback
    plain = "Your weekly AI digest is ready. View this email in HTML mode for the full experience."
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    sent = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    print(f"[Send] Email sent — Message ID: {sent['id']}")
    return sent["id"]


if __name__ == "__main__":
    test_html = """
    <html><body style="font-family:Arial;padding:20px;background:#F7F3EE;">
    <h1 style="color:#7D2240;font-family:Georgia,serif;">Test Digest Email</h1>
    <p style="color:#6B6560;">If you see this in your inbox, the Gmail API send is working!</p>
    <p style="color:#C9A847;font-weight:bold;">— Social Pipeline Test</p>
    </body></html>
    """
    send_email("Test — Social Pipeline Digest", test_html)
    print("Test email sent successfully!")
