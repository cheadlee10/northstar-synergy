import imaplib
import email
from email.header import decode_header
import os

SAVE_DIR = r"C:\Users\chead\.openclaw\workspace"

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login("clawcliff@gmail.com", "zpon bjsp dnfx tkdy")
mail.select('"[Gmail]/Spam"')

status, messages = mail.search(None, "ALL")
ids = messages[0].split()

for eid in ids:
    status, msg_data = mail.fetch(eid, "(RFC822)")
    raw = msg_data[0][1]
    msg = email.message_from_bytes(raw)
    subj = msg["Subject"] or ""
    frm = msg["From"] or ""
    
    for part in msg.walk():
        cd = part.get_content_disposition()
        if cd and "attachment" in cd:
            fname = part.get_filename()
            if fname:
                out_path = os.path.join(SAVE_DIR, fname)
                with open(out_path, "wb") as f:
                    f.write(part.get_payload(decode=True))
                print(f"SAVED: {out_path} (from: {frm}, subj: {subj})", flush=True)

mail.logout()
print("DONE", flush=True)
