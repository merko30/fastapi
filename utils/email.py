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
