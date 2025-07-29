import logging
from typing import Optional

import sendgrid
from sendgrid.helpers.mail import Mail

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_password_reset_email(email: str, reset_token: str) -> bool:
    """Send password reset email using SendGrid"""
    try:
        if settings.SENDGRID_API_KEY == "changeme":
            logger.warning("SendGrid API key not configured - email not sent")
            return False

        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Reroute Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2563eb;">Reroute</h1>
                </div>
                
                <h2 style="color: #1f2937;">Reset Your Password</h2>
                
                <p>You requested to reset your password for your Reroute account.</p>
                
                <p>Click the button below to reset your password:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #2563eb; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p>Or copy this link into your browser:</p>
                <p style="word-break: break-all; color: #6b7280;">{reset_url}</p>
                
                <p><strong>This link expires in 1 hour.</strong></p>
                
                <hr style="margin: 30px 0; border: 1px solid #e5e7eb;">
                
                <p style="color: #6b7280; font-size: 14px;">
                    If you didn't request this password reset, you can safely ignore this email.
                    Your password will remain unchanged.
                </p>
                
                <p style="color: #6b7280; font-size: 14px;">
                    Best regards,<br>
                    The Reroute Team
                </p>
            </div>
        </body>
        </html>
        """

        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=email,
            subject="Reset Your Reroute Password",
            html_content=html_content,
        )

        response = sg.send(message)
        logger.info(
            f"Password reset email sent to {email}, status: {response.status_code}"
        )
        return response.status_code == 202

    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        return False


def send_welcome_email(email: str, name: Optional[str] = None) -> bool:
    """Send welcome email to new users"""
    try:
        if settings.SENDGRID_API_KEY == "changeme":
            logger.warning("SendGrid API key not configured - email not sent")
            return False

        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

        display_name = name if name else "there"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Reroute</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2563eb;">Reroute</h1>
                </div>
                
                <h2 style="color: #1f2937;">Welcome to Reroute, {display_name}! 🚴‍♂️</h2>
                
                <p>Thank you for joining Reroute, your AI-powered cycling training assistant!</p>
                
                <p>Here's what you can do with Reroute:</p>
                <ul>
                    <li>📊 <strong>Connect your Strava account</strong> to sync your rides and activities</li>
                    <li>🤖 <strong>Get AI-powered training plans</strong> tailored to your goals</li>
                    <li>🗺️ <strong>Discover amazing routes</strong> in your area</li>
                    <li>📈 <strong>Track your progress</strong> and improve your performance</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.FRONTEND_URL}" 
                       style="background-color: #2563eb; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                        Get Started
                    </a>
                </div>
                
                <p>Happy cycling!</p>
                
                <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                    Best regards,<br>
                    The Reroute Team
                </p>
            </div>
        </body>
        </html>
        """

        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=email,
            subject="Welcome to Reroute - Your AI Cycling Assistant!",
            html_content=html_content,
        )

        response = sg.send(message)
        logger.info(f"Welcome email sent to {email}, status: {response.status_code}")
        return response.status_code == 202

    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        return False
