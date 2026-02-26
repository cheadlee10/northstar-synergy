import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

FROM_EMAIL = "clawcliff@gmail.com"
APP_PASSWORD = "zpon bjsp dnfx tkdy"
TO_EMAIL = "chead@me.com"

subject = "8wk V28 Formula Fix — B2B/Pickup Bridge"

html = """
<html><body style="font-family: Calibri, Arial, sans-serif; font-size: 14px; color: #222;">

<p>Craig,</p>

<p>Here's the updated formula for <strong>V28</strong> (and a new companion row for True Misc).
The current version computes B2B/Pickup as a <em>residual</em>, which lets True Misc bleed in
and break the bridge. The fix pulls East B2B and West Pickup directly.</p>

<hr style="border:1px solid #ccc; margin: 16px 0;">

<h3 style="color:#1a3c6e;">V28 — B2B + Pickup (replace existing formula)</h3>
<p style="background:#f4f4f4; padding:12px; border-left:4px solid #1a3c6e; font-family:Courier New, monospace; font-size:12px; white-space:pre-wrap;">=IFERROR(
  LET(
    Dt,  INT(INDEX($16:$16, COLUMN())),
    Wk,  INDEX($17:$17, COLUMN()),
    r,   MATCH(1,
           INDEX(
             (INT('by Facility_wk'!$B$1:$B$10318)=Dt) *
             ('by Facility_wk'!$C$1:$C$10318=Wk) *
             ('by Facility_wk'!$D$1:$D$10318=""),
             0),
           0),
    Den, INDEX($D$51:$I$51, MATCH(Dt, INT($D$5:$I$5), 0)),
    (
      INDEX('by Facility_wk'!$F$1:$F$10318, r)
    + INDEX('by Facility_wk'!$G$1:$G$10318, r)
    ) / Den
  ),
0)</p>

<p><strong>What changed:</strong> Instead of inferring B2B+Pickup as a residual,
this directly pulls:<br>
&nbsp;&nbsp;• Col F = <code>Sum of east.B2B_Commissions</code><br>
&nbsp;&nbsp;• Col G = <code>Sum of west.PickUps</code><br>
Divided by budget volume (row 51) — same denominator as before.</p>

<hr style="border:1px solid #ccc; margin: 16px 0;">

<h3 style="color:#1a3c6e;">New row — True Misc (insert below V28, adjust row references accordingly)</h3>
<p style="background:#f4f4f4; padding:12px; border-left:4px solid #c0392b; font-family:Courier New, monospace; font-size:12px; white-space:pre-wrap;">=IFERROR(
  LET(
    Dt,  INT(INDEX($16:$16, COLUMN())),
    Wk,  INDEX($17:$17, COLUMN()),
    r,   MATCH(1,
           INDEX(
             (INT('by Facility_wk'!$B$1:$B$10318)=Dt) *
             ('by Facility_wk'!$C$1:$C$10318=Wk) *
             ('by Facility_wk'!$D$1:$D$10318=""),
             0),
           0),
    Den, INDEX($D$51:$I$51, MATCH(Dt, INT($D$5:$I$5), 0)),
    INDEX('by Facility_wk'!$AC$1:$AC$10318, r) / Den
  ),
0)</p>

<p><strong>What it does:</strong> Pulls True Misc (col AC = col 29 of
<code>by Facility_wk</code>) directly as its own CPP line.
This isolates the W6→W7 swing ($457K → $35K = $0.064/pkg) so it
doesn't distort the B2B/Pickup line.</p>

<hr style="border:1px solid #ccc; margin: 16px 0;">

<h3 style="color:#1a3c6e;">Why the bridge wasn't footing</h3>
<table style="border-collapse:collapse; width:100%;">
  <tr style="background:#1a3c6e; color:white;">
    <th style="padding:6px 10px; text-align:left;">Item</th>
    <th style="padding:6px 10px; text-align:right;">W6</th>
    <th style="padding:6px 10px; text-align:right;">W7</th>
    <th style="padding:6px 10px; text-align:right;">Swing</th>
  </tr>
  <tr style="background:#f9f9f9;">
    <td style="padding:6px 10px;">True Misc $</td>
    <td style="padding:6px 10px; text-align:right;">$456,635</td>
    <td style="padding:6px 10px; text-align:right;">$34,574</td>
    <td style="padding:6px 10px; text-align:right; color:#c0392b;">-$422,061</td>
  </tr>
  <tr>
    <td style="padding:6px 10px;">True Misc CPP impact (÷ budget vol)</td>
    <td style="padding:6px 10px; text-align:right;">+$0.070</td>
    <td style="padding:6px 10px; text-align:right;">+$0.005</td>
    <td style="padding:6px 10px; text-align:right; color:#c0392b;">-$0.064</td>
  </tr>
  <tr style="background:#f9f9f9;">
    <td style="padding:6px 10px;">Old V28 result</td>
    <td style="padding:6px 10px; text-align:right;">$0.304</td>
    <td style="padding:6px 10px; text-align:right;">$0.165</td>
    <td style="padding:6px 10px; text-align:right; color:#c0392b;">-$0.139</td>
  </tr>
  <tr>
    <td style="padding:6px 10px; color:#1a6e3c;"><strong>New V28 result (direct pull)</strong></td>
    <td style="padding:6px 10px; text-align:right; color:#1a6e3c;"><strong>~$0.098</strong></td>
    <td style="padding:6px 10px; text-align:right; color:#1a6e3c;"><strong>~$0.098</strong></td>
    <td style="padding:6px 10px; text-align:right; color:#1a6e3c;"><strong>stable</strong></td>
  </tr>
</table>

<br>
<p>One note: double-check that col F and col G in <code>by Facility_wk</code> are
what you expect (East B2B Commissions and West Pickups) on your end — column
indices confirmed from the file you sent but worth a spot check before rolling in.</p>

<p>— Cliff</p>

</body></html>
"""

msg = MIMEMultipart("alternative")
msg["From"] = f"Cliff <{FROM_EMAIL}>"
msg["To"] = TO_EMAIL
msg["Subject"] = subject
msg.attach(MIMEText(html, "html"))

with smtplib.SMTP("smtp.gmail.com", 587) as s:
    s.starttls()
    s.login(FROM_EMAIL, APP_PASSWORD)
    s.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())

print("Sent.")
