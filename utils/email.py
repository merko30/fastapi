import os
import resend

resend.api_key = os.environ["RESEND_API_KEY"]


def send_email(to: str, subject: str, html: str):
    params: resend.Emails.SendParams = {
        "to": [to],
        "from": "Coachapp <onboarding@resend.dev>",
        "html": html,
        "subject": subject,
    }
    email = resend.Emails.send(params)

    return email


def send_mail_to(email_address: str) -> str:
    if os.environ("ENV") == "production":
        return email_address

    return os.environ("RESEND_DEV_EMAIL")
