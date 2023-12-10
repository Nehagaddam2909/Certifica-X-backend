import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email(sender_email, sender_password, recipient_email, subject, message, attachment_path):
    # Create a multipart message
    email_message = MIMEMultipart()
    email_message['From'] = sender_email
    email_message['To'] = recipient_email
    email_message['Subject'] = subject

    # Add the message body
    email_message.attach(MIMEText(message, 'plain'))

    # Attach the file
    with open(attachment_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {attachment_path}")
        email_message.attach(part)

    # Configure the SMTP server
    smtp_server = 'smtp.gmail.com'  # Replace with your SMTP server

    # Create a secure connection to the SMTP server
    server = smtplib.SMTP(smtp_server, 587)
    server.starttls()

    # Login to the email account
    server.login(sender_email, sender_password)

    # Send the email
    server.send_message(email_message)

    # Close the connection
    server.quit()

    print('Email sent successfully!')



smail = input("From: ")
sender_email = smail
pswd = input("Pswd: ")
sender_password = pswd  # not your actual mail password, your gmail accounts app password generate through setting of your account fron security in 2-factor verification
rmail = input("To: ")
recipient_email = rmail
subject = input("Subject: ")
message = input("Message: ")
attachment_path = 'C:/Users/USER/Desktop/Mails/sample.pdf'  # Replace with the path to your attachment

# Call the send_email function
send_email(sender_email, sender_password, recipient_email, subject, message, attachment_path)
