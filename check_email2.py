import imaplib
import email
from email.header import decode_header
import sys

try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login("clawcliff@gmail.com", "zpon bjsp dnfx tkdy")
    
    # List all folders
    status, folders = mail.list()
    print("FOLDERS:", flush=True)
    for f in folders:
        print(f"  {f.decode()}", flush=True)
    
    # Check All Mail
    mail.select('"[Gmail]/All Mail"')
    status, messages = mail.search(None, "ALL")
    ids = messages[0].split()
    print(f"\nAll Mail total: {len(ids)}", flush=True)
    
    if ids:
        latest = ids[-5:]
        for eid in reversed(latest):
            status, msg_data = mail.fetch(eid, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            subj = msg["Subject"] or "(no subject)"
            frm = msg["From"] or ""
            date = msg["Date"] or ""
            attachments = []
            for part in msg.walk():
                cd = part.get_content_disposition()
                if cd and "attachment" in cd:
                    fname = part.get_filename()
                    if fname:
                        attachments.append(fname)
            print(f"FROM={frm} | DATE={date} | SUBJ={subj} | ATTACH={attachments}", flush=True)

    mail.logout()
except Exception as e:
    print(f"ERROR: {e}", flush=True)
