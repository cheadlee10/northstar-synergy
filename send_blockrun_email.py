import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

FROM_EMAIL = "clawcliff@gmail.com"
APP_PASSWORD = "zpon bjsp dnfx tkdy"
TO_EMAIL = "vicky@blockrun.ai"

subject = "Wallet Balance Sync Issue - BlockRun ClawRouter"

html_body = """
<html>
  <body style="font-family: Arial, sans-serif;">
    <h2>BlockRun ClawRouter Wallet Sync Issue</h2>
    
    <p>Hi Vicky,</p>
    
    <p>We have a wallet that received USDC on Base network, but ClawRouter's API is showing a $0.00 balance despite the funds being confirmed on-chain.</p>
    
    <p><strong>Details:</strong></p>
    <ul>
      <li><strong>Wallet Address:</strong> 0x123Bc89eC5110E10ce28aC6B8c8d10F3aa00ce80</li>
      <li><strong>Amount:</strong> 5.5875 USDC</li>
      <li><strong>Network:</strong> Base (L2)</li>
      <li><strong>Status:</strong> Confirmed on BaseScan at 8:31 AM UTC on 2026-02-25</li>
      <li><strong>ClawRouter Report:</strong> $0.00 balance (using FREE model)</li>
      <li><strong>Time Elapsed:</strong> 90+ minutes since confirmation</li>
    </ul>
    
    <p>The funds are definitely on Base (verified via BaseScan), but BlockRun's indexer hasn't picked them up yet. We'd appreciate a manual refresh of the wallet balance index.</p>
    
    <p>Can you help us get this resolved quickly? We're ready to start routing once the balance syncs.</p>
    
    <p>Thanks,<br/>
    Cliff<br/>
    NorthStar Synergy</p>
  </body>
</html>
"""

try:
    msg = MIMEMultipart("alternative")
    msg["From"] = f"Cliff <{FROM_EMAIL}>"
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))
    
    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls()
        s.login(FROM_EMAIL, APP_PASSWORD)
        s.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
    
    print("[OK] Email sent to", TO_EMAIL)
except Exception as e:
    print("[ERROR]", str(e))
