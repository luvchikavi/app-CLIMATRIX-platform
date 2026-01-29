"""
Email service for transactional emails.
Supports SMTP with TLS (SendGrid, Gmail, etc.)
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails."""

    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
        self.use_tls = settings.smtp_use_tls

    @property
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        return bool(self.host and self.user and self.password)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email
            text_content: Plain text fallback (optional)

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning("Email not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD")
            # In development, log the email content instead
            logger.info(f"[DEV] Would send email to {to_email}: {subject}")
            logger.info(f"[DEV] Content: {text_content or html_content[:500]}")
            return True  # Return True in dev mode to not block workflows

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Add plain text part
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)

            # Add HTML part
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            # Send
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str) -> bool:
        """Send password reset email with reset link."""
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"

        subject = "Reset Your CLIMATRIX Password"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #10b981; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
                .button {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>CLIMATRIX</h1>
                </div>
                <div class="content">
                    <h2>Password Reset Request</h2>
                    <p>Hi {user_name},</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p>This link will expire in {settings.password_reset_token_expire_minutes} minutes.</p>
                    <p>If you didn't request this password reset, you can safely ignore this email.</p>
                    <p>Best regards,<br>The CLIMATRIX Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from CLIMATRIX. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Password Reset Request

        Hi {user_name},

        We received a request to reset your password. Visit the link below to create a new password:

        {reset_url}

        This link will expire in {settings.password_reset_token_expire_minutes} minutes.

        If you didn't request this password reset, you can safely ignore this email.

        Best regards,
        The CLIMATRIX Team
        """

        return self.send_email(to_email, subject, html_content, text_content)

    def send_welcome_email(self, to_email: str, user_name: str, org_name: str) -> bool:
        """Send welcome email to new users."""
        login_url = f"{settings.frontend_url}/login"

        subject = f"Welcome to CLIMATRIX, {user_name}!"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #10b981; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
                .button {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>CLIMATRIX</h1>
                </div>
                <div class="content">
                    <h2>Welcome to CLIMATRIX!</h2>
                    <p>Hi {user_name},</p>
                    <p>Your account has been created for <strong>{org_name}</strong>.</p>
                    <p>CLIMATRIX helps you track, manage, and report your organization's greenhouse gas emissions
                       across Scope 1, 2, and 3.</p>
                    <p style="text-align: center;">
                        <a href="{login_url}" class="button">Get Started</a>
                    </p>
                    <p>If you have any questions, our team is here to help.</p>
                    <p>Best regards,<br>The CLIMATRIX Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from CLIMATRIX. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to CLIMATRIX!

        Hi {user_name},

        Your account has been created for {org_name}.

        CLIMATRIX helps you track, manage, and report your organization's greenhouse gas emissions
        across Scope 1, 2, and 3.

        Get started: {login_url}

        If you have any questions, our team is here to help.

        Best regards,
        The CLIMATRIX Team
        """

        return self.send_email(to_email, subject, html_content, text_content)

    async def send_invitation_email(
        self,
        to_email: str,
        invitation_token: str,
        organization_name: str,
        inviter_name: str,
    ) -> bool:
        """Send invitation email to join an organization."""
        invite_url = f"{settings.frontend_url}/accept-invitation?token={invitation_token}"

        subject = f"You're invited to join {organization_name} on CLIMATRIX"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #10b981; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
                .button {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>CLIMATRIX</h1>
                </div>
                <div class="content">
                    <h2>You're Invited!</h2>
                    <p>Hi there,</p>
                    <p><strong>{inviter_name}</strong> has invited you to join <strong>{organization_name}</strong> on CLIMATRIX.</p>
                    <p>CLIMATRIX helps organizations track, manage, and report their greenhouse gas emissions
                       across Scope 1, 2, and 3.</p>
                    <p style="text-align: center;">
                        <a href="{invite_url}" class="button">Accept Invitation</a>
                    </p>
                    <p>This invitation will expire in 7 days.</p>
                    <p>If you weren't expecting this invitation, you can safely ignore this email.</p>
                    <p>Best regards,<br>The CLIMATRIX Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from CLIMATRIX. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        You're Invited to CLIMATRIX!

        Hi there,

        {inviter_name} has invited you to join {organization_name} on CLIMATRIX.

        CLIMATRIX helps organizations track, manage, and report their greenhouse gas emissions
        across Scope 1, 2, and 3.

        Accept your invitation: {invite_url}

        This invitation will expire in 7 days.

        If you weren't expecting this invitation, you can safely ignore this email.

        Best regards,
        The CLIMATRIX Team
        """

        return self.send_email(to_email, subject, html_content, text_content)


# Singleton instance
email_service = EmailService()
