import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

FROM_EMAIL = "clawcliff@gmail.com"
APP_PASSWORD = "zpon bjsp dnfx tkdy"

# Send to multiple contacts
recipients = [
    "vicky@blockrun.ai",
    "support@blockrun.ai",
    "hello@blockrun.ai"
]

subject = "[URGENT] Wallet balance not syncing - blocking production"

html_body = """
<html>
  <body style="font-family: Arial, sans-serif;">
    <p><strong>[URGENT FOLLOW-UP]</strong></p>
    
    <p>Sent USDC deposit 2+ hours ago (confirmed on-chain). ClawRouter shows $0 balance. Please manually refresh wallet indexer.</p>
    
    <p>This is blocking production use.</p>
    
    <p>Thanks,<br/>
    Cliff</p>
  </body>
</html>
"""

for recipient in recipients:
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"Cliff <{FROM_EMAIL}>"
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(FROM_EMAIL, APP_PASSWORD)
            s.sendmail(FROM_EMAIL, recipient, msg.as_string())
        
        print(f"[OK] Email sent to {recipient}")
    except Exception as e:
        print(f"[ERROR] {recipient}: {str(e)}")
