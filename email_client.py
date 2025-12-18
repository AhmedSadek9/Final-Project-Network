import smtplib
import imaplib
import email
import socket
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header

# Mail Server Configuration (ethereal.email)
SMTP_SERVER = "smtp.ethereal.email"
SMTP_PORT = 587

IMAP_SERVER = "imap.ethereal.email"
IMAP_PORT = 993

# Notification Server Configuration
NOTIFICATION_HOST = "127.0.0.1"
NOTIFICATION_PORT = 9999

# Notification Client Function
def send_notification(message):
    """
    Sends a short notification message to the local TCP notification server.
    """
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(2) # Prevent hanging if server is offline
        client_socket.connect((NOTIFICATION_HOST, NOTIFICATION_PORT))
        client_socket.sendall(message.encode("utf-8"))
        client_socket.close()
        print(f" Notification  sent: {message}")
    except socket.error as e:
        print(f"Notification has error  : {e}")


# SMTP: Send Email Function
def send_email(sender_email, password, receiver_email, subject, body):
    """
    Sends an email using SMTP protocol via Ethereal.
    """
    start_time = time.time()

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Establish SMTP connection
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(sender_email, password)

        # Send email
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        elapsed_time = time.time() - start_time

        print("\n Email sent successfully to Ethereal!")
        print(f"SMTP Latency: {elapsed_time:.4f} seconds")

        send_notification("Email Sent Successfully")
        return True, elapsed_time

    except Exception as e:
        print(f"\n Failed to send email: {e}")
        send_notification("Email Sending Failed")
        return False, 0


# IMAP: Receive Latest Email Function
def receive_latest_email(email_address, password):
    """
    Fetches the latest email from Ethereal inbox using IMAP.
    """
    start_time = time.time()
    mail = None

    try:
        # Establish IMAP SSL connection
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(email_address, password)
        mail.select("inbox")

        # Search for all messages
        status, messages = mail.search(None, "ALL")
        message_ids = messages[0].split()

        if not message_ids:
            print(" Inbox is empty")
            return False, 0

        latest_id = message_ids[-1]

        # Fetch latest email
        status, data = mail.fetch(latest_id, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Decode subject
        subject_data = decode_header(msg["Subject"])[0]
        subject = (
            subject_data[0].decode(subject_data[1] or "utf-8")
            if isinstance(subject_data[0], bytes)
            else subject_data[0]
        )

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

        elapsed_time = time.time() - start_time

        print("\n Latest Email Received from Ethereal")
        print(f" Subject: {subject}")
        print(f" Body (preview):\n{body[:200]}...")
        print(f" IMAP Latency: {elapsed_time:.4f} seconds")

        send_notification("Email Received Successfully")
        return True, elapsed_time

    except Exception as e:
        print(f"\n Failed to receive email: {e}")
        send_notification("Email Receiving Failed")
        return False, 0

    finally:
        if mail:
            try:
                mail.logout()
            except:
                pass


# Main Execution
if __name__ == "__main__":


    # ⚠️ Configuration
    SENDER_EMAIL = "morgan.nikolaus51@ethereal.email" 
    SENDER_PASSWORD = "5aHNAbGYaeG5PANkYQ"
    RECEIVER_EMAIL = SENDER_EMAIL  # Testing by sending to me

    SUBJECT = f"Network Project Test - {time.strftime('%H:%M:%S')}"
    BODY = "Testing SMTP/IMAP protocols with Ethereal server."

    print("\nSMTP: Sending Email")
    send_success, _ = send_email(
        SENDER_EMAIL,
        SENDER_PASSWORD,
        RECEIVER_EMAIL,
        SUBJECT,
        BODY,
    )
    if send_success:
        print("\nWaiting for delivery")
        time.sleep(5)
        print("\nIMAP: Receiving Email")
        receive_latest_email(SENDER_EMAIL, SENDER_PASSWORD)
        
        
        
        #python email_client.py