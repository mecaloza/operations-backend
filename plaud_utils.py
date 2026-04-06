from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from models import Transcript, TranscriptAttachment

HTML_BREAK_RE = re.compile(r"<(br|/p|/div|/li|/tr|/h[1-6])\b[^>]*>", re.IGNORECASE)
HTML_STRIP_RE = re.compile(r"<[^>]+>")
STYLE_BLOCK_RE = re.compile(r"<style\b.*?</style>", re.IGNORECASE | re.DOTALL)
SCRIPT_BLOCK_RE = re.compile(r"<script\b.*?</script>", re.IGNORECASE | re.DOTALL)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
MULTISPACE_RE = re.compile(r"[ \t]+")
MULTIBREAK_RE = re.compile(r"\n{3,}")
METADATA_LINE_RE = re.compile(r"^(subject|from|received at|attachments?)\s*:\s*", re.IGNORECASE)
CSS_GARBAGE_RE = re.compile(r"(^|\n)(?:\.[\w-]+\s*\{|@media\b|body\s*\{|table\s*\{|td\s*\{|font-family\s*:|color\s*:)", re.IGNORECASE)


def normalize_whitespace(text: str | None) -> str | None:
    if text is None:
        return None
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = MULTISPACE_RE.sub(" ", text)
    text = MULTIBREAK_RE.sub("\n\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = text.strip()
    return text or None


def html_to_text(html_content: str | None) -> str | None:
    if not html_content:
        return None
    text = COMMENT_RE.sub(" ", html_content)
    text = STYLE_BLOCK_RE.sub(" ", text)
    text = SCRIPT_BLOCK_RE.sub(" ", text)
    text = HTML_BREAK_RE.sub("\n", text)
    text = HTML_STRIP_RE.sub(" ", text)
    text = html.unescape(text)
    return normalize_whitespace(text)


def strip_metadata_lines(text: str | None) -> str | None:
    if not text:
        return None
    lines = []
    for line in text.split("\n"):
        if METADATA_LINE_RE.match(line.strip()):
            continue
        lines.append(line)
    return normalize_whitespace("\n".join(lines))


def looks_like_html_garbage(text: str | None) -> bool:
    if not text:
        return False
    if "<html" in text.lower() or "<body" in text.lower() or "<table" in text.lower():
        return True
    return bool(CSS_GARBAGE_RE.search(text))


def clean_email_text(text: str | None) -> str | None:
    if not text:
        return None
    candidate = html_to_text(text) if looks_like_html_garbage(text) or "<" in text else text
    candidate = strip_metadata_lines(candidate)
    return normalize_whitespace(candidate)


def normalize_role(role: str | None, filename: str | None, content_type: str | None) -> str:
    role_value = (role or "").lower().strip()
    name = (filename or "").lower()
    ctype = (content_type or "").lower()
    if role_value in {"summary", "transcript", "image", "other"}:
        return role_value
    if any(token in name for token in ["summary", "resumen"]):
        return "summary"
    if any(token in name for token in ["transcript", "transcripcion", "transcripción", "meeting"]):
        return "transcript"
    if ctype.startswith("image/") or Path(name).suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic"}:
        return "image"
    return "other"


def attachment_public_payload(transcript_id: int, attachment: TranscriptAttachment) -> dict[str, Any]:
    metadata = json.loads(attachment.attachment_metadata_json) if attachment.attachment_metadata_json else None
    role = normalize_role(attachment.attachment_role, attachment.filename, attachment.content_type)
    return {
        "id": attachment.id,
        "filename": attachment.filename,
        "content_type": attachment.content_type,
        "size_bytes": attachment.size_bytes or 0,
        "attachment_role": role,
        "storage_path": attachment.storage_path,
        "content_text": attachment.content_text,
        "content_hash": attachment.content_hash,
        "is_inline": attachment.is_inline,
        "attachment_metadata": metadata,
        "created_at": attachment.created_at,
        "download_url": f"/api/v1/transcripts/{transcript_id}/attachments/{attachment.id}",
        "preview_url": f"/api/v1/transcripts/{transcript_id}/attachments/{attachment.id}?disposition=inline",
        "is_previewable": role == "image" or (attachment.content_type or "").startswith("text/"),
    }


def transcript_primary_text(transcript: Transcript) -> str:
    summary = clean_email_text(transcript.summary_full)
    full = clean_email_text(transcript.transcript_full)
    content = clean_email_text(transcript.content)

    sections: list[str] = []
    if summary:
        sections.append(f"## Resumen\n\n{summary}")
    if full:
        sections.append(f"## Transcripción\n\n{full}")
    if content and content not in {summary, full}:
        sections.append(content)
    if sections:
        return "\n\n".join(sections)
    return transcript.title or "Transcript"


def transcript_display_summary(transcript: Transcript) -> str | None:
    summary = clean_email_text(transcript.summary_full)
    if summary:
        return summary
    content = clean_email_text(transcript.content)
    if not content:
        return None
    return content[:280] + ("..." if len(content) > 280 else "")
