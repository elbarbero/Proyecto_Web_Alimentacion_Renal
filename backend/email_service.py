import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL

def send_email(to_email, subject, body):
    """
    Helper genérico para enviar emails.
    """
    print(f"--- Intentando enviar email a {to_email} ---\nSubject: {subject}\n-------------------------------")
    msg = MIMEMultipart()
    msg['From'] = f"Web Renal (No-Reply) <{SENDER_EMAIL}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        if not SENDER_PASSWORD or SENDER_PASSWORD == "TU_CONTRASEÑA_AQUI":
            print(">> ERROR: Faltan credenciales en el archivo .env")
            return False, "Missing credentials in .env"

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()
        
        print(">> Email enviado CORRECTAMENTE.")
        return True, "Email sent successfully"
        
    except Exception as e:
        print(f">> ERROR CRÍTICO enviando email: {e}")
        return False, f"Failed to send email: {e}"

def send_email_notification(feedback_text):
    """
    Envía un correo con la sugerencia (wrapper legacy).
    """
    subject = "Nueva Sugerencia - Web Alimentación Renal"
    return send_email(RECIPIENT_EMAIL, subject, feedback_text)
