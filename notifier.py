import smtplib, requests, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST","smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT",587))
SMTP_USER = os.getenv("SMTP_USER","")
SMTP_PASS = os.getenv("SMTP_PASS","")
FROM_EMAIL = os.getenv("FROM_EMAIL",SMTP_USER)
FIREBASE_SERVER_KEY = os.getenv("FIREBASE_SERVER_KEY","")
FCM_URL = "https://fcm.googleapis.com/fcm/send"

def build_email_html(hackathons):
    items = ""
    for h in hackathons:
        items += f"""<div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin-bottom:16px;">
            <span style="background:#6200ea;color:white;font-size:11px;padding:2px 8px;border-radius:12px;">{h.get('source','')}</span>
            <h3 style="margin:8px 0 4px;">{h.get('title','')}</h3>
            <p style="color:#666;font-size:13px;margin:0 0 4px;">Deadline: {h.get('deadline','TBD')}</p>
            <p style="color:#388e3c;font-size:13px;margin:0 0 12px;">Prize: {h.get('prize','N/A')}</p>
            <a href="{h.get('url','')}" style="background:#6200ea;color:white;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;">View Hackathon →</a>
        </div>"""
    return f"""<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <div style="background:#6200ea;padding:20px;border-radius:8px;margin-bottom:24px;">
            <h1 style="color:white;margin:0;font-size:22px;">🚀 New Hackathons Found!</h1>
            <p style="color:#e0e0e0;margin:4px 0 0;">{len(hackathons)} new hackathon(s) just dropped</p>
        </div>{items}</body></html>"""

def send_email_notification(to_emails, hackathons):
    if not SMTP_USER or not SMTP_PASS or not hackathons or not to_emails: return
    html = build_email_html(hackathons)
    subject = f"🚀 {len(hackathons)} New Hackathon{'s' if len(hackathons)>1 else ''} Just Dropped!"
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls(); server.login(SMTP_USER, SMTP_PASS)
        for email in to_emails:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject; msg["From"] = FROM_EMAIL; msg["To"] = email
            msg.attach(MIMEText(html,"html"))
            server.sendmail(FROM_EMAIL, email, msg.as_string())
            print(f"[Email] Sent to {email}")
        server.quit()
    except Exception as e:
        print(f"[Email] Error: {e}")

def send_push_notification(fcm_tokens, hackathons):
    if not FIREBASE_SERVER_KEY or not hackathons or not fcm_tokens: return
    first = hackathons[0]; count = len(hackathons)
    title = f"🚀 {count} New Hackathon{'s' if count>1 else ''}!"
    body = first.get("title","New hackathon available")
    if count > 1: body += f" + {count-1} more"
    for token in fcm_tokens:
        try:
            requests.post(FCM_URL,
                headers={"Authorization":f"key={FIREBASE_SERVER_KEY}","Content-Type":"application/json"},
                json={"to":token,"notification":{"title":title,"body":body},"data":{"url":first.get("url","")}},
                timeout=10)
        except Exception as e:
            print(f"[FCM] {e}")
