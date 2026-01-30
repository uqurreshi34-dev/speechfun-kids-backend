import traceback
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings


def send_verification_email(user, token):
    """Send email verification link using SendGrid API"""
    verification_url = f"{settings.SITE_URL}/verify-email?token={token}"

    # Plain text version (important for spam filters!)
    plain_text = f"""
    Hi {user.username}!

    Welcome to SpeechFun Kids! 

    Please verify your email by clicking this link:
    {verification_url}

    This link expires in 24 hours.

    If you didn't create an account, please ignore this email.

    Thanks,
    The SpeechFun Kids Team
        """

    message = Mail(
        from_email=(settings.EMAIL_FROM, 'SpeechFun Kids'),  # Add sender name
        to_emails=user.email,
        subject='Verify Your SpeechFun Kids Account',  # Remove emoji from subject
        plain_text_content=plain_text,  # Add plain text version
        html_content=f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f0f0f0;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; border: 1px solid #e5e7eb;">
                    <h1 style="color: #7c3aed; font-size: 24px;">Welcome to SpeechFun Kids!</h1>
                    <p style="font-size: 16px; color: #374151;">Hi {user.username},</p>
                    <p style="font-size: 16px; color: #374151;">Thanks for joining SpeechFun Kids! Please verify your email address to get started.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}"
                           style="background-color: #7c3aed;
                                  color: white;
                                  padding: 15px 30px;
                                  text-decoration: none;
                                  border-radius: 8px;
                                  font-weight: bold;
                                  display: inline-block;
                                  font-size: 16px;">
                            Verify My Email
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #6b7280;">Or copy and paste this link into your browser:</p>
                    <p style="background-color: #f3f4f6; padding: 12px; border-radius: 5px; word-break: break-all; font-size: 14px; color: #374151;">
                        {verification_url}
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                    
                    <p style="color: #9ca3af; font-size: 12px; margin-top: 20px;">
                        This link expires in 24 hours. If you didn't create an account with SpeechFun Kids, you can safely ignore this email.
                    </p>
                    
                    <p style="color: #9ca3af; font-size: 12px;">
                        Best regards,<br>
                        The SpeechFun Kids Team
                    </p>
                </div>
            </body>
        </html>
        """
    )

    try:
        sg = SendGridAPIClient(settings.EMAIL_HOST_PASSWORD)
        response = sg.send(message)

        print(f"✅ SendGrid accepted email")
        print(f"   Status code: {response.status_code}")
        print(f"   To: {user.email}")
        print(f"   Message ID: {response.headers.get('X-Message-Id', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ SendGrid API error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False
