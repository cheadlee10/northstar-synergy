import imaplib
import email
from email.header import decode_header

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login("clawcliff@gmail.com", "zpon bjsp dnfx tkdy")

# Check spam
mail.select('"[Gmail]/Spam"')
status, messages = mail.search(None, "ALL")
ids = messages[0].split()
print(f"Spam count: {len(ids)}", flush=True)
for eid in reversed(ids[-5:] if ids else []):
    status, msg_data = mail.fetch(eid, "(RFC822)")
    raw = msg_data[0][1]
    msg = email.message_from_bytes(raw)
    subj = msg["Subject"] or "(no subject)"
    frm = msg["From"] or ""
    attachments = [p.get_filename() for p in msg.walk() if p.get_content_disposition() and "attachment" in p.get_content_disposition() and p.get_filename()]
    print(f"FROM={frm} | SUBJ={subj} | ATTACH={attachments}", flush=True)

mail.logout()
