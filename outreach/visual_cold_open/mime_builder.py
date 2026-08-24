# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — RFC 2822 MIME builder.

Builds a multipart message (multipart/mixed → multipart/alternative[text, html] +
image attachment) and encodes it base64URL for the Gmail API's `message.raw` field.
Pure stdlib (`email.*`); no send capability lives here.
"""
from __future__ import annotations

import base64
from email.message import EmailMessage
from typing import Optional, Tuple


def build_message(
    from_addr: str,
    to_addr: str,
    subject: str,
    plaintext: str,
    html: str,
    attachment: Optional[Tuple[str, bytes, str]] = None,
) -> EmailMessage:
    """Assemble an EmailMessage.

    `attachment` is (filename, data_bytes, mime_type) or None. When present it is
    added as a downloadable attachment (Content-Disposition: attachment). The text
    and html parts form the alternative body.
    """
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject

    # Plain text is the base content; add_alternative(html) makes it multipart/alternative.
    msg.set_content(plaintext or "")
    if html:
        msg.add_alternative(html, subtype="html")

    if attachment is not None:
        filename, data, mime_type = attachment
        if not data:
            raise ValueError("attachment data is empty")
        maintype, _, subtype = (mime_type or "application/octet-stream").partition("/")
        subtype = subtype or "octet-stream"
        msg.add_attachment(
            data, maintype=maintype, subtype=subtype, filename=filename
        )
    return msg


def to_raw_base64url(msg: EmailMessage) -> str:
    """Encode a message as URL-safe base64 (with standard '=' padding, which the Gmail
    API's `message.raw` field accepts) for a draft's raw MIME."""
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


def build_raw(
    from_addr: str,
    to_addr: str,
    subject: str,
    plaintext: str,
    html: str,
    attachment: Optional[Tuple[str, bytes, str]] = None,
) -> str:
    """Convenience: build the message and return its base64URL raw string."""
    return to_raw_base64url(
        build_message(from_addr, to_addr, subject, plaintext, html, attachment)
    )


def has_attachment(msg: EmailMessage) -> bool:
    return any(part.get_content_disposition() == "attachment" for part in msg.walk())
