from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# ========== CHANGE ONLY THESE 3 LINES ==========
MAIL_USERNAME = 'your-email@gmail.com'      # LINE 1: Change to YOUR Gmail
MAIL_PASSWORD = 'your-16-char-app-password' # LINE 2: Change to YOUR App Password
RECIPIENT_EMAIL = 'your-email@gmail.com'    # LINE 3: Change to YOUR Gmail (same as above)
# ==============================================

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD

mail = Mail(app)

with app.app_context():
    try:
        msg = Message('Test Email from ConsultantEase', 
                      recipients=[RECIPIENT_EMAIL],
                      body='This is a test email. Your email system is working!')
        mail.send(msg)
        print('✅ Email sent successfully! Check your inbox.')
    except Exception as e:
        print(f'❌ Failed to send email: {e}')