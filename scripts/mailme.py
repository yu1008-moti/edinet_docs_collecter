import os
import smtplib

import smtplib, ssl
from email.mime.text import MIMEText

# 送信先のアドレスを登録します
send_address = os.getenv('GMAIL_ADDRESS')
password = os.getenv('PYTHON_GMAIL_PASSWORD')

# メインの関数になります
def send_email_abount_accomplish(additional_info):
  msg = make_mime_text(
    mail_to = send_address,
    subject = "処理完了の通知",
    body = f"Pythonでのメール送信です。追加情報: {additional_info}"
  )
  send_gmail(msg)

def send_email_abount_error(e):
  msg = make_mime_text(
    mail_to = send_address,
    subject = "処理エラーの通知",
    body = f"Pythonでのメール送信です。エラー内容: {e}"
  )
  send_gmail(msg)

# 件名、送信先アドレス、本文を渡す関数です
def make_mime_text(mail_to, subject, body):
  msg = MIMEText(body, "html")
  msg["Subject"] = subject
  msg["To"] = mail_to
  msg["From"] = send_address
  return msg

# smtp経由でメール送信する関数です
def send_gmail(msg):
  server = smtplib.SMTP_SSL(
    "smtp.gmail.com", 465,
    context = ssl.create_default_context())
  server.set_debuglevel(0)
  server.login(send_address, password)
  server.send_message(msg)