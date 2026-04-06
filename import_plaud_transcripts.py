#!/usr/bin/env python3
"""
Backfill/import de transcripts de Plaud AI desde Gmail hacia Operations Dashboard.

Características:
- Recorre correos históricos (ALL), no solo unread.
- Dedup estable por Message-ID / fallback hash.
- Extrae body, transcript txt, summary txt e imágenes/diagramas.
- Guarda cache local de adjuntos y metadata rica en DB.
- Reimporta/enriquece transcripts existentes sin duplicarlos.

Uso:
    python3 import_plaud_transcripts.py --dry-run
    python3 import_plaud_transcripts.py --limit 20
    python3 import_plaud_transcripts.py --since 2026-03-01
    python3 import_plaud_transcripts.py --mailbox '[Gmail]/Todos'
"""

from __future__ import annotations

import argparse
import email
import hashlib
import imaplib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import joinedload

from dotenv import load_dotenv

load_dotenv()

from database import SessionLocal
from models import Project, Transcript, TranscriptAttachment
from plaud_utils import clean_email_text, normalize_role, transcript_primary_text

DEFAULT_GMAIL_ENV = Path("/Users/lukeskywalker/.openclaw/workspace/.secrets/gmail.env")
DEFAULT_ATTACHMENT_DIR = Path(__file__).resolve().parent / "storage" / "plaud"
PLAUD_SENDERS = {"noreply@plaud.ai", "no-reply@plaud.ai", "hello@plaud.ai", "support@plaud.ai"}
TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic"}
PROJECT_MAPPING = {
    "ax": "action-experience",
    "action experience": "action-experience",
    "operations": "operations",
    "ops": "operations",
    "colleague": "action-colleague",
    "action colleague": "action-colleague",
    "newton ai": "newton-ai",
    "newton": "newton-ai",
    "da vinci": "operations",
    "otro": "operations",
    "n/a": "operations",
}


@dataclass
class ExtractedAttachment:
    filename: str
    content_type: str | None
    size_bytes: int
    attachment_role: str
    payload_bytes: bytes
    content_text: str | None
    content_hash: str
    storage_path: str | None
    is_inline: bool
    metadata: dict


@dataclass
class ExtractedEmail:
    title: str
    content_markdown: str
    raw_email: str | None
    transcript_full: str | None
    summary_full: str | None
    message_id: str | None
    thread_key: str | None
    dedup_key: str
    email_from: str | None
    email_subject: str | None
    email_received_at: datetime | None
    source_payload: dict
    attachments: list[ExtractedAttachment]
    project_slugs: list[str]
    tags: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Importa transcripts Plaud desde Gmail")
    parser.add_argument("--dry-run", action="store_true", help="No escribe en DB")
    parser.add_argument("--limit", type=int, default=None, help="Límite de correos a procesar")
    parser.add_argument("--since", type=str, default=None, help="Fecha mínima YYYY-MM-DD")
    parser.add_argument("--mailbox", type=str, default='[Gmail]/Todos', help="Mailbox IMAP a leer")
    parser.add_argument("--env-file", type=str, default=str(DEFAULT_GMAIL_ENV), help="Ruta a gmail.env")
    parser.add_argument("--attachment-dir", type=str, default=str(DEFAULT_ATTACHMENT_DIR), help="Directorio local para adjuntos")
    parser.add_argument("--message-id", type=str, default=None, help="Procesar un Message-ID específico")
    parser.add_argument("--include-non-plaud-sender", action="store_true", help="Acepta correos que parezcan Plaud aunque el sender no coincida exacto")
    parser.add_argument("--reprocess-existing", action="store_true", help="Recalcula transcripts Plaud ya importados sin volver a leer Gmail")
    return parser.parse_args()


def load_gmail_credentials(env_file: Path) -> tuple[str, str]:
    if env_file.exists():
        load_dotenv(env_file, override=True)

    email_addr = os.getenv("GMAIL_EMAIL")
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    if not email_addr or not app_password:
        raise RuntimeError("Faltan GMAIL_EMAIL / GMAIL_APP_PASSWORD en gmail.env")
    return email_addr, app_password


def decode_mime(value: str | None) -> str:
    if not value:
        return ""
    decoded_parts = email.header.decode_header(value)
    chunks: list[str] = []
    for chunk, encoding in decoded_parts:
        if isinstance(chunk, bytes):
            chunks.append(chunk.decode(encoding or "utf-8", errors="replace"))
        else:
            chunks.append(chunk)
    return "".join(chunks).strip()


def normalize_whitespace(text: str | None) -> str | None:
    if text is None:
        return None
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() or None


def slugify_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return value[:180] or "attachment"


def attachment_role(filename: str | None, content_type: str | None) -> str:
    lower_name = (filename or "").lower()
    lower_type = (content_type or "").lower()
    if "summary" in lower_name or "resumen" in lower_name:
        return "summary"
    if "transcript" in lower_name or "meeting" in lower_name:
        return "transcript"
    if lower_type.startswith("image/") or any(lower_name.endswith(ext) for ext in IMAGE_EXTENSIONS):
        return "image"
    return "other"


def parse_received_at(message: Message) -> datetime | None:
    raw_date = message.get("Date")
    if not raw_date:
        return None
    try:
        dt = parsedate_to_datetime(raw_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def extract_sender(message: Message) -> str | None:
    from_header = decode_mime(message.get("From"))
    return from_header or None


def sender_matches_plaud(message: Message, include_non_plaud_sender: bool = False) -> bool:
    senders = [addr.lower() for _, addr in getaddresses(message.get_all("From", [])) if addr]
    subject = decode_mime(message.get("Subject"))
    if any(addr in PLAUD_SENDERS or "plaud" in addr for addr in senders):
        return True
    if include_non_plaud_sender and ("plaud" in subject.lower()):
        return True
    return False


def html_to_text(html: str) -> str:
    return clean_email_text(html) or ""


def iter_message_parts(message: Message) -> Iterable[Message]:
    if message.is_multipart():
        for part in message.walk():
            if part.is_multipart():
                continue
            yield part
    else:
        yield message


def extract_body_text(message: Message) -> tuple[str | None, str | None]:
    plain_parts: list[str] = []
    html_parts: list[str] = []
    for part in iter_message_parts(message):
        disposition = (part.get_content_disposition() or "").lower()
        if disposition == "attachment":
            continue
        content_type = (part.get_content_type() or "").lower()
        payload = part.get_payload(decode=True) or b""
        charset = part.get_content_charset() or "utf-8"
        text = payload.decode(charset, errors="replace")
        if content_type == "text/plain":
            plain_parts.append(text)
        elif content_type == "text/html":
            html_parts.append(text)

    plain = normalize_whitespace("\n\n".join(plain_parts))
    html = normalize_whitespace("\n\n".join(html_to_text(chunk) for chunk in html_parts if chunk.strip()))
    return plain, html


def detect_projects(*texts: str | None) -> list[str]:
    detected: list[str] = []
    combined = "\n".join(filter(None, texts)).lower()
    for token, slug in PROJECT_MAPPING.items():
        if token in combined and slug not in detected:
            detected.append(slug)
    if not detected:
        detected.append("operations")
    return detected


def detect_title(subject: str | None, transcript_text: str | None, fallback: str) -> str:
    for candidate in [subject, transcript_text, fallback]:
        if not candidate:
            continue
        line = normalize_whitespace(candidate.split("\n", 1)[0])
        if line:
            cleaned = re.sub(r"^\[Plaud-AutoFlow\]\s*", "", line, flags=re.I)
            cleaned = re.sub(r"^(plaud\s*(ai)?\s*[-:|]\s*)", "", cleaned, flags=re.I)
            cleaned = re.sub(r"^\d{2}-\d{2}\s+", "", cleaned)
            return cleaned[:500]
    return fallback[:500]


def build_dedup_key(message_id: str | None, subject: str | None, received_at: datetime | None, raw_email: str | None) -> str:
    if message_id:
        normalized = message_id.strip().lower().strip("<>")
        return f"gmail:{normalized}"
    base = "|".join([
        (subject or "").strip().lower(),
        received_at.isoformat() if received_at else "",
        hashlib.sha256((raw_email or "").encode("utf-8", errors="ignore")).hexdigest()[:24],
    ])
    return f"gmail-hash:{hashlib.sha256(base.encode('utf-8')).hexdigest()}"


def persist_attachment(base_dir: Path, dedup_key: str, filename: str, payload: bytes) -> str:
    safe_dir = base_dir / slugify_filename(dedup_key.replace(":", "-"))
    safe_dir.mkdir(parents=True, exist_ok=True)
    safe_name = slugify_filename(filename)
    target = safe_dir / safe_name
    target.write_bytes(payload)
    return str(target)


def extract_attachments(message: Message, base_dir: Path, dedup_key: str, dry_run: bool) -> list[ExtractedAttachment]:
    items: list[ExtractedAttachment] = []
    for part in iter_message_parts(message):
        filename = decode_mime(part.get_filename())
        disposition = (part.get_content_disposition() or "").lower()
        content_type = part.get_content_type()
        payload = part.get_payload(decode=True) or b""
        if not payload:
            continue
        is_attachment = disposition == "attachment" or bool(filename)
        if not is_attachment:
            continue

        name = filename or f"part-{len(items)+1}"
        role = normalize_role(attachment_role(name, content_type), name, content_type)
        ext = Path(name).suffix.lower()
        content_text = None
        if ext in TEXT_EXTENSIONS or (content_type or "").startswith("text/"):
            charset = part.get_content_charset() or "utf-8"
            content_text = normalize_whitespace(payload.decode(charset, errors="replace"))
        content_hash = hashlib.sha256(payload).hexdigest()
        storage_path = None if dry_run else persist_attachment(base_dir, dedup_key, name, payload)
        items.append(
            ExtractedAttachment(
                filename=name,
                content_type=content_type,
                size_bytes=len(payload),
                attachment_role=role,
                payload_bytes=payload,
                content_text=content_text,
                content_hash=content_hash,
                storage_path=storage_path,
                is_inline=disposition == "inline",
                metadata={
                    "content_disposition": disposition or None,
                    "content_id": part.get("Content-ID"),
                    "charset": part.get_content_charset(),
                },
            )
        )
    return items


def choose_text_by_role(attachments: list[ExtractedAttachment], role: str) -> str | None:
    candidates = [a.content_text for a in attachments if a.attachment_role == role and a.content_text]
    if not candidates:
        return None
    return max(candidates, key=len)


def build_markdown(title: str, subject: str | None, sender: str | None, received_at: datetime | None, body_text: str | None, summary_text: str | None, transcript_text: str | None, attachments: list[ExtractedAttachment]) -> str:
    del subject, sender, received_at
    blocks = [f"# {title}"]
    if summary_text:
        blocks.append("## Resumen\n\n" + summary_text)
    if transcript_text:
        blocks.append("## Transcripción\n\n" + transcript_text)
    if body_text and body_text not in {summary_text, transcript_text}:
        blocks.append("## Notas del correo\n\n" + body_text)
    visible_attachments = [att for att in attachments if att.attachment_role not in {"summary", "transcript"}]
    if visible_attachments:
        items = []
        for att in visible_attachments:
            descriptor = f"- {att.filename}"
            if att.attachment_role:
                descriptor += f" ({att.attachment_role})"
            if att.content_type:
                descriptor += f" [{att.content_type}]"
            if att.size_bytes:
                descriptor += f" - {att.size_bytes} bytes"
            items.append(descriptor)
        blocks.append("## Adjuntos\n\n" + "\n".join(items))
    return "\n\n".join(block for block in blocks if block).strip()


def extract_email_record(message: Message, attachment_dir: Path, dry_run: bool) -> ExtractedEmail:
    subject = decode_mime(message.get("Subject")) or "Plaud transcript"
    sender = extract_sender(message)
    received_at = parse_received_at(message)
    body_plain, body_html = extract_body_text(message)
    raw_email = clean_email_text(body_plain or body_html)
    message_id = decode_mime(message.get("Message-ID")) or None
    thread_key = decode_mime(message.get("X-GM-THRID")) or None
    dedup_key = build_dedup_key(message_id, subject, received_at, raw_email)
    attachments = extract_attachments(message, attachment_dir, dedup_key, dry_run=dry_run)
    summary_full = clean_email_text(choose_text_by_role(attachments, "summary"))
    transcript_full = clean_email_text(choose_text_by_role(attachments, "transcript"))

    body_for_content = clean_email_text(body_plain or body_html)
    if not summary_full and body_for_content:
        summary_full = body_for_content
    if not transcript_full and body_for_content:
        transcript_full = body_for_content

    title = detect_title(subject, transcript_full, "Plaud transcript")
    content_markdown = build_markdown(title, subject, sender, received_at, raw_email, summary_full, transcript_full, attachments)
    project_slugs = detect_projects(subject, raw_email, summary_full, transcript_full)

    tags = ["plaud", "gmail-import"]
    for slug in project_slugs:
        tags.append(slug)
    if message_id:
        tags.append(f"message-id:{message_id.strip('<>')}")

    source_payload = {
        "headers": {
            "message_id": message_id,
            "subject": subject,
            "from": sender,
            "date": received_at.isoformat() if received_at else None,
        },
        "project_slugs": project_slugs,
        "attachment_count": len(attachments),
    }

    return ExtractedEmail(
        title=title,
        content_markdown=content_markdown,
        raw_email=raw_email,
        transcript_full=transcript_full,
        summary_full=summary_full,
        message_id=message_id,
        thread_key=thread_key,
        dedup_key=dedup_key,
        email_from=sender,
        email_subject=subject,
        email_received_at=received_at,
        source_payload=source_payload,
        attachments=attachments,
        project_slugs=project_slugs,
        tags=",".join(dict.fromkeys(tags)),
    )


def connect_gmail(email_addr: str, app_password: str) -> imaplib.IMAP4_SSL:
    client = imaplib.IMAP4_SSL("imap.gmail.com")
    client.login(email_addr, app_password)
    return client


def search_message_uids(client: imaplib.IMAP4_SSL, mailbox: str, since: str | None, limit: int | None) -> list[bytes]:
    mailboxes = [mailbox]
    if mailbox == '[Gmail]/Todos':
        mailboxes.extend(['[Gmail]/All Mail', 'All Mail', 'INBOX'])
    elif mailbox == '[Gmail]/All Mail':
        mailboxes.extend(['[Gmail]/Todos', 'All Mail', 'INBOX'])

    selected_mailbox = None
    for candidate in mailboxes:
        mailbox_name = candidate if candidate.startswith('"') else f'"{candidate}"'
        status, _ = client.select(mailbox_name, readonly=True)
        if status == "OK":
            selected_mailbox = candidate
            break

    if not selected_mailbox:
        raise RuntimeError(f"No se pudo abrir mailbox {mailbox}")

    criteria = ['ALL']
    if since:
        dt = datetime.strptime(since, "%Y-%m-%d")
        criteria.extend(['SINCE', dt.strftime('%d-%b-%Y')])
    status, data = client.uid('search', None, *criteria)
    if status != "OK":
        raise RuntimeError("IMAP search falló")
    uids = data[0].split() if data and data[0] else []
    if limit:
        uids = uids[-limit:]
    return list(reversed(uids))


def fetch_messages(client: imaplib.IMAP4_SSL, uids: list[bytes]) -> Iterable[Message]:
    for uid in uids:
        status, data = client.uid("fetch", uid, "(RFC822)")
        if status != "OK" or not data:
            continue
        raw_bytes = None
        for item in data:
            if isinstance(item, tuple) and item[1]:
                raw_bytes = item[1]
                break
        if not raw_bytes:
            continue
        yield email.message_from_bytes(raw_bytes)


def sync_transcript(record: ExtractedEmail, dry_run: bool, attachment_dir: Path) -> tuple[str, str]:
    db = SessionLocal()
    try:
        projects = {project.slug: project for project in db.query(Project).all()}
        project_objs = [projects[slug] for slug in record.project_slugs if slug in projects]
        if not project_objs:
            project_objs = [projects["operations"]] if "operations" in projects else []
        if not project_objs:
            raise RuntimeError("No hay proyectos válidos en la DB para asociar el transcript")

        query = db.query(Transcript).filter(Transcript.source_dedup_key == record.dedup_key)
        transcript = query.first()
        if not transcript and record.message_id:
            transcript = db.query(Transcript).filter(Transcript.source_message_id == record.message_id).first()

        action = "update" if transcript else "create"
        if dry_run:
            return action, record.title

        if not transcript:
            transcript = Transcript(
                title=record.title,
                content=record.content_markdown,
                project_id=project_objs[0].id,
                created_by="Plaud AI Gmail Import",
                tags=record.tags,
                file_size=len(record.content_markdown.encode("utf-8")),
                version=1,
                is_latest=True,
                source_type="gmail",
                source_message_id=record.message_id,
                source_thread_id=record.thread_key,
                source_dedup_key=record.dedup_key,
            )
            db.add(transcript)
            db.flush()
        else:
            transcript.title = record.title
            transcript.content = record.content_markdown
            transcript.tags = record.tags
            transcript.file_size = len(record.content_markdown.encode("utf-8"))
            transcript.project_id = project_objs[0].id

        transcript.source_payload_json = json.dumps(record.source_payload, ensure_ascii=False)
        transcript.raw_email = clean_email_text(record.raw_email)
        transcript.transcript_full = clean_email_text(record.transcript_full)
        transcript.summary_full = clean_email_text(record.summary_full)
        transcript.email_from = record.email_from
        transcript.email_subject = record.email_subject
        transcript.email_received_at = record.email_received_at
        transcript.attachments_json = json.dumps([
            {
                "filename": item.filename,
                "content_type": item.content_type,
                "size_bytes": item.size_bytes,
                "attachment_role": item.attachment_role,
                "storage_path": item.storage_path,
                "content_hash": item.content_hash,
                "is_inline": item.is_inline,
                "metadata": item.metadata,
            }
            for item in record.attachments
        ], ensure_ascii=False)
        transcript.projects = project_objs

        db.flush()

        existing_by_hash = {item.content_hash: item for item in transcript.attachments}
        seen_hashes: set[str] = set()
        for item in record.attachments:
            seen_hashes.add(item.content_hash)
            attachment = existing_by_hash.get(item.content_hash)
            if not attachment:
                attachment = TranscriptAttachment(transcript_id=transcript.id, filename=item.filename)
                db.add(attachment)
            attachment.filename = item.filename
            attachment.content_type = item.content_type
            attachment.size_bytes = item.size_bytes
            attachment.attachment_role = item.attachment_role
            attachment.storage_path = item.storage_path
            attachment.content_text = item.content_text
            attachment.content_hash = item.content_hash
            attachment.is_inline = item.is_inline
            attachment.attachment_metadata_json = json.dumps(item.metadata, ensure_ascii=False)

        for stale in list(transcript.attachments):
            if stale.content_hash and stale.content_hash not in seen_hashes:
                db.delete(stale)

        transcript.content = transcript_primary_text(transcript)
        transcript.file_size = len(transcript.content.encode("utf-8"))

        db.commit()
        return action, record.title
    finally:
        db.close()


def reprocess_existing_transcripts(dry_run: bool = False) -> None:
    db = SessionLocal()
    stats = {"reprocessed": 0}
    try:
        transcripts = db.query(Transcript).options(joinedload(Transcript.attachments)).filter(
            Transcript.source_type == "gmail"
        ).all()
        for transcript in transcripts:
            transcript.summary_full = clean_email_text(transcript.summary_full)
            transcript.transcript_full = clean_email_text(transcript.transcript_full)
            transcript.raw_email = clean_email_text(transcript.raw_email)
            if transcript.attachments_json:
                try:
                    snapshot = json.loads(transcript.attachments_json)
                except json.JSONDecodeError:
                    snapshot = []
                normalized = []
                for item in snapshot:
                    normalized.append({
                        **item,
                        "attachment_role": normalize_role(item.get("attachment_role"), item.get("filename"), item.get("content_type")),
                    })
                transcript.attachments_json = json.dumps(normalized, ensure_ascii=False)
            for attachment in transcript.attachments:
                attachment.attachment_role = normalize_role(attachment.attachment_role, attachment.filename, attachment.content_type)
                attachment.content_text = clean_email_text(attachment.content_text)
            transcript.content = transcript_primary_text(transcript)
            transcript.file_size = len(transcript.content.encode("utf-8"))
            stats["reprocessed"] += 1
        if dry_run:
            db.rollback()
        else:
            db.commit()
    finally:
        db.close()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    if dry_run:
        print("DRY-RUN: no se escribieron cambios en DB")


def process_mailbox(args: argparse.Namespace) -> None:
    if args.reprocess_existing:
        reprocess_existing_transcripts(dry_run=args.dry_run)
        return

    env_file = Path(args.env_file)
    attachment_dir = Path(args.attachment_dir)
    if not args.dry_run:
        attachment_dir.mkdir(parents=True, exist_ok=True)

    email_addr, app_password = load_gmail_credentials(env_file)
    client = connect_gmail(email_addr, app_password)
    stats = {"processed": 0, "created": 0, "updated": 0, "skipped": 0}

    try:
        uids = search_message_uids(client, args.mailbox, args.since, args.limit)
        for message in fetch_messages(client, uids):
            if args.message_id:
                current_message_id = decode_mime(message.get("Message-ID"))
                if (current_message_id or "").strip() != args.message_id.strip():
                    continue
            if not sender_matches_plaud(message, include_non_plaud_sender=args.include_non_plaud_sender):
                stats["skipped"] += 1
                continue
            record = extract_email_record(message, attachment_dir=attachment_dir, dry_run=args.dry_run)
            action, title = sync_transcript(record, dry_run=args.dry_run, attachment_dir=attachment_dir)
            stats["processed"] += 1
            stats[f"{action}d"] += 1
            print(f"[{action.upper()}] {title} :: {record.dedup_key}")
    finally:
        try:
            client.logout()
        except Exception:
            pass

    print("\nResumen:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    if args.dry_run:
        print("DRY-RUN: no se escribieron cambios en DB ni en disco")


if __name__ == "__main__":
    try:
        process_mailbox(parse_args())
    except KeyboardInterrupt:
        print("\nCancelado por usuario")
        sys.exit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
