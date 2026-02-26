import imaplib
import email
import os
from email.header import decode_header

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('clawcliff@gmail.com', 'zpon bjsp dnfx tkdy')
mail.select('"[Gmail]/Spam"')

status, messages = mail.search(None, 'ALL')
ids = messages[0].split()

for mid in ids:
    status, msg_data = mail.fetch(mid, '(RFC822)')
    msg = email.message_from_bytes(msg_data[0][1])
    for part in msg.walk():
        filename = part.get_filename()
        if filename and filename.endswith('.xlsx'):
            payload = part.get_payload(decode=True)
            save_path = 'C:/Users/chead/.openclaw/workspace/CCH_new.xlsx'
            with open(save_path, 'wb') as f:
                f.write(payload)
            print(f'Saved: {save_path} ({len(payload)} bytes)')

mail.logout()
