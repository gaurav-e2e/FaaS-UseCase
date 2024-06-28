import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def send_email(recipient, otp):
    # Fetch SMTP server details from environment variables
    smtp_server = os.environ['SMTP_SERVER']
    smtp_port = int(os.environ['SMTP_PORT'])
    smtp_username = os.environ['SMTP_USERNAME']
    smtp_password = os.environ['SMTP_PASSWORD']
    sender_email = os.environ['SENDER_EMAIL']

    # Create the email message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your OTP for verification"
    message["From"] = sender_email
    message["To"] = recipient

    # Create the plain-text and HTML version of your message
    text = f"Your OTP is: {otp}"
    html = f"""\
    <html>
      <body>
        <p>Your OTP is: <strong>{otp}</strong></p>
      </body>
    </html>
    """

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    message.attach(part1)
    message.attach(part2)

    try:
        # Create secure connection with server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient, message.as_string())
        logger.info(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Error sending email to {recipient}: {str(e)}")
        return False

def handle(event, context):
    logger.info("E2E function invoked")
    
    try:
        payload = json.loads(event.body)
    except json.JSONDecodeError:
        logger.error("Failed to parse event body as JSON")
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid JSON in request body')
        }
    
    # Extract email and OTP from payload
    recipient_email = payload.get('email')
    otp = payload.get('otp')
    
    if not recipient_email or not otp:
        logger.warning("Missing email or OTP in payload")
        return {
            'statusCode': 400,
            'body': json.dumps('Email and OTP are required')
        }
    
    logger.info(f"Attempting to send email to {recipient_email}")
    
    # Send email
    email_sent = send_email(recipient_email, otp)
    
    if email_sent:
        logger.info("Email sent successfully")
        return {
            'statusCode': 200,
            'body': json.dumps('Email sent successfully')
        }
    else:
        logger.error("Failed to send email")
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to send email')
        }
