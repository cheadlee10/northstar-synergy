import imaplib, email
from email.header import decode_header

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('Clawcliff@gmail.com', 'zpon bjsp dnfx tkdy')

found_attachment = None

for folder in ['INBOX', '"[Gmail]/Spam"', '"[Gmail]/Sent Mail"']:
    try:
        status, _ = mail.select(folder)
        _, msgs = mail.search(None, 'ALL')
        all_ids = msgs[0].decode().split() if msgs[0].strip() else []
        print(f'=== {folder}: {len(all_ids)} messages ===')
        for msg_id in all_ids[-20:]:
            _, msg_data = mail.fetch(msg_id, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            raw_subj = decode_header(msg.get('Subject','') or '')[0][0]
            subject = raw_subj.decode() if isinstance(raw_subj, bytes) else (raw_subj or '')
            sender = msg.get('From','')
            date = msg.get('Date','')
            for part in msg.walk():
                cd = part.get_content_disposition() or ''
                if 'attachment' in cd:
                    fname = part.get_filename() or ''
                    print(f'  [{folder}] From={sender} | {date} | Subj={subject[:40]} | ATTACH={fname}')
                    if fname.lower().endswith(('.xlsx','.xls')) and any(k in fname.upper() for k in ['CCH','WBR','COST','FILE']):
                        found_attachment = (part, fname)
    except Exception as e:
        print(f'Error on {folder}: {e}')

if found_attachment:
    part, fname = found_attachment
    with open('C:/Users/chead/OneDrive/Documents/CCH_Files_clean.xlsx','wb') as f:
        f.write(part.get_payload(decode=True))
    print('SAVED')
else:
    print('NO_MATCH_ANYWHERE')

mail.logout()
