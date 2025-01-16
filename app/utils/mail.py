import smtplib
from email.mime.text import MIMEText
from app.core.config import settings


async def user_mail_event(mail_task_data):
    msg = MIMEText(
        f"Please verify your email using this token: {mail_task_data.body.token}"
    )
    msg["Subject"] = "Email Verification"
    msg["From"] = settings.smtp_from
    msg["To"] = mail_task_data.user.email

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_tls:
                server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(
                settings.smtp_from, mail_task_data.user.email, msg.as_string()
            )
    except Exception as e:
        print(f"Error sending email: {e}")


def send_overdue_email(email, subject, detail):
    msg = MIMEText(detail)
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = email

    try:
        print("Email sent to: ", email)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_tls:
                server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, email, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
