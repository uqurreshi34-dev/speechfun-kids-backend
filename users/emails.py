from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings
from django.utils.html import strip_tags


def send_verification_email(user, token):
    """Send email verification link using SendGrid API"""
    verification_url = f"{settings.SITE_URL}/verify-email?token={token}"

    message = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=user.email,
        subject="Verify Your SpeechFun Kids Account! 🎉",
        html_content=f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f0f0f0;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                    <h1 style="color: #7c3aed;">Welcome to SpeechFun Kids!</h1>
                    <p>Hi {user.username}!</p>
                    <p>Thanks for joining! Click below to verify your email:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background: linear-gradient(to right, #7c3aed, #ec4899); 
                                  color: white; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 10px; 
                                  font-weight: bold; display: inline-block;">
                            Verify My Email ✅
                        </a>
                    </div>
                    <p>Or copy this link:</p>
                    <p style="background-color: #f3f4f6; padding: 10px; border-radius: 5px; word-break: break-all;">
                        {verification_url}
                    </p>
                    <p style="color: #666; font-size: 12px; margin-top: 30px;">
                        Link expires in 24 hours. If this wasn't you, ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
    )

    try:
        sg = SendGridAPIClient(settings.EMAIL_HOST_PASSWORD)  # your API key
        response = sg.send(message)
        print(f"✅ Email sent! Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ SendGrid API error: {e}")
        return False
