import imaplib
import email
from email.header import decode_header
import sys

try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login("clawcliff@gmail.com", "zpon bjsp dnfx tkdy")
    mail.select("inbox")

    status, messages = mail.search(None, "ALL")
    ids = messages[0].split()
    print(f"Total emails: {len(ids)}", flush=True)
    latest = ids[-10:]

    for eid in reversed(latest):
        status, msg_data = mail.fetch(eid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        subj_raw = msg["Subject"] or ""
        try:
            subj = decode_header(subj_raw)[0][0]
            if isinstance(subj, bytes):
                subj = subj.decode("utf-8", errors="replace")
        except:
            subj = subj_raw

        frm = msg["From"] or ""
        date = msg["Date"] or ""

        attachments = []
        for part in msg.walk():
            cd = part.get_content_disposition()
            if cd and "attachment" in cd:
                fname = part.get_filename()
                if fname:
                    attachments.append(fname)

        print(f"ID={eid.decode()} | FROM={frm} | DATE={date} | SUBJ={subj} | ATTACH={attachments}", flush=True)

    mail.logout()
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    sys.stdout.flush()
