from email_service import send_email

send_email(
    "pujasharmab122@gmail.com",
    "Email Automation Test",
    """
Hello,

This is a test email from the Employee Workflow Management System.

Email automation is working successfully.

Thank you,
Employee Workflow Management System
"""
)

print("Email sent successfully")