import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

FROM_EMAIL   = "clawcliff@gmail.com"
APP_PASSWORD = "zpon bjsp dnfx tkdy"
TO_EMAIL     = "C963146@ontrac.com"
FILE_PATH    = r"C:\Users\chead\OneDrive\Documents\RBS_Savings_Analysis.xlsx"

SUBJECT = "RBS Pilot — Savings Analysis | 11 Highlighted Facilities"

HTML = """
<html><body style="font-family:Calibri,Arial,sans-serif;font-size:14px;color:#1F3864;">
<p>Craig,</p>

<p>Attached is the RBS savings analysis for the 11 pilot facilities discussed this morning.</p>

<h3 style="color:#2F5597;">Headline Numbers</h3>
<table style="border-collapse:collapse;width:500px;">
  <tr style="background:#2F5597;color:white;">
    <th style="padding:8px 12px;text-align:left;">Metric</th>
    <th style="padding:8px 12px;text-align:right;">Value</th>
  </tr>
  <tr style="background:#EBF3FB;">
    <td style="padding:6px 12px;font-weight:bold;">Total Annual Savings (11 Facilities)</td>
    <td style="padding:6px 12px;text-align:right;font-weight:bold;color:#375623;">$14,339,952</td>
  </tr>
  <tr>
    <td style="padding:6px 12px;">Average CPP Improvement</td>
    <td style="padding:6px 12px;text-align:right;">$0.43/pkg</td>
  </tr>
  <tr style="background:#EBF3FB;">
    <td style="padding:6px 12px;">Highest Savings Facility</td>
    <td style="padding:6px 12px;text-align:right;">Sacramento — $1,692,617</td>
  </tr>
  <tr>
    <td style="padding:6px 12px;">Largest CPP Gap</td>
    <td style="padding:6px 12px;text-align:right;">Columbus — $0.785/pkg</td>
  </tr>
</table>

<h3 style="color:#2F5597;">What's Driving the Savings</h3>
<p>Three components explain most of the CPP gap between RBS and stop payment:</p>
<ol>
  <li><strong>Route Density (Pieces/Route):</strong> Facilities with fewer packages per route pay more per package under stop payment. Columbus (138.5 pcs/route) has the largest CPP gap ($0.785) — each stop covers fewer packages, making the per-stop charge expensive per unit. Under RBS, the fixed route cost is spread more efficiently.</li>
  <li><strong>Route Length (Miles):</strong> Longer routes amplify savings. Columbus (145.9 mi/route) and Atlanta (109.5 mi/route) absorb more gas &amp; maintenance cost, which is contained in the fixed RBS rate vs. uncapped under stop payment.</li>
  <li><strong>Stop Fee Rate at Low-Density Sites:</strong> Pittsburgh, Boise, and Petaluma stack both effects — low density AND higher stop fee rates = largest RBS advantage on a CPP basis ($0.56–$0.63/pkg).</li>
</ol>
<p><em>Dense metro sites (Queens 238 pcs/route, JFK 194, Northern NJ 193) also benefit, primarily through labor cost containment — short routes, high labor/day, RBS caps total spend cleanly.</em></p>

<h3 style="color:#2F5597;">Workbook Contents</h3>
<ul>
  <li><strong>Executive Summary</strong> — KPI tiles + full comparison table (RBS CPP vs Stop Payment CPP, savings per facility)</li>
  <li><strong>Savings Drivers</strong> — Component table with color-coded density and mileage heat map; key findings narrative</li>
  <li><strong>Chart Data</strong> — Two bar charts: Annual Savings by Facility and CPP Gap by Facility</li>
</ul>

<br>
<p style="color:#595959;font-size:12px;">Cliff | Financial Analysis</p>
</body></html>
"""

msg = MIMEMultipart("alternative")
msg["From"]    = f"Cliff <{FROM_EMAIL}>"
msg["To"]      = TO_EMAIL
msg["Subject"] = SUBJECT
msg.attach(MIMEText(HTML, "html"))

# Attach Excel
with open(FILE_PATH, "rb") as f:
    part = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="RBS_Savings_Analysis.xlsx"')
    msg.attach(part)

with smtplib.SMTP("smtp.gmail.com", 587) as s:
    s.starttls()
    s.login(FROM_EMAIL, APP_PASSWORD)
    s.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())

print("SENT", flush=True)
