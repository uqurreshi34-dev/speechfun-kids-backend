import socket
import traceback
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags


def send_verification_email(user, token):
    """Send email verification link to user"""
    verification_url = f"{settings.SITE_URL}/verify-email?token={token}"

    subject = "Verify Your SpeechFun Kids Account!"

    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f0f0f0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                <h1 style="color: #7c3aed;">Welcome to SpeechFun Kids! 🎉</h1>
                <p>Hi {user.username}!</p>
                <p>Thanks for joining SpeechFun Kids! Click the button below to verify your email:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background: linear-gradient(to right, #7c3aed, #ec4899); 
                              color: white; 
                              padding: 15px 30px; 
                              text-decoration: none; 
                              border-radius: 10px; 
                              font-weight: bold;
                              display: inline-block;">
                        Verify My Email ✅
                    </a>
                </div>
                <p>Or copy this link:</p>
                <p style="background-color: #f3f4f6; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {verification_url}
                </p>
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    This link expires in 24 hours. If you didn't create an account, ignore this email.
                </p>
            </div>
        </body>
    </html>
    """

    plain_message = strip_tags(html_message)

    # Set timeout for socket operations
    socket.setdefaulttimeout(10)

    try:
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        if result == 1:  # send_mail returns number of emails sent
            print(f"✅ Email sent successfully to {user.email}")
            return True
        else:
            print("❌ Email sending failed - no emails sent")
            return False

    except socket.timeout:
        print("❌ Email sending timed out - SMTP server not responding")
        return False
    except Exception as e:
        print(f"❌ Email sending failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False
    finally:
        socket.setdefaulttimeout(None)
