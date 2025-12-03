from fastapi import APIRouter, BackgroundTasks
from apps.main.config import *
import smtplib
from jinja2 import Template
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi.templating import Jinja2Templates
import os
from apps.main.database.db import get_db 
from apps.main.models.model import * 

router = APIRouter()
templates_dir = "apps/main/front_end/templates"  

# def get_all_to_address():
#     db = next(get_db())
#     alert_setting = db.query(settings).filter(settings.id == 1).first()
#     if alert_setting and alert_setting.to_address:
#         return alert_setting.to_address
#     return []

def send_email(subject, email_message, cam_msg, kit_msg, store_msg, temp_msg):
    try:
        db=next(get_db())
        print("Mail function called for ",subject)
        to_email_addresses = email_message['to_addresses']
        if not to_email_addresses:
            print("No email addresses found in the database.")
            return
        
        email_data = {
            "greeting": "Hello Team",
            "subject": subject,
            "lpu_id": email_message["lpu_id"],
            "lpu_name": email_message["lpu_name"],
            "sender_name": "Team cosai",
        }
        print("email_data:",email_data)
        if cam_msg:
            email_data["camera_ip"] = email_message["camera_ip"]
            email_data["camera_status"] = email_message["camera_status"]
        elif kit_msg:
            print("!!! In kit status mail")
            email_data["kit_status"] = email_message["kit_status"]
            email_data["lpu_ip"] = email_message["lpu_ip"]
        elif store_msg:  
            email_data["total_disk_gb"] = email_message["total_disk_gb"]
            email_data["used_disk_gb"] = email_message["used_disk_gb"]
            email_data["free_disk_gb"] = email_message["free_disk_gb"]
            email_data["storage_status"] = email_message["storage_status"]
        elif temp_msg:
            email_data["cpu_temperature"] = email_message["cpu_temperature"]

        # Read Template
        template_path = os.path.join(templates_dir, "mail/email_template.html")
        print("in tamplate:")
        with open(template_path, "r") as file:
            template_str = file.read()
        
        jinja_template = Template(template_str)
        email_content = jinja_template.render(email_data)
        
        print("***********d******************",to_email_addresses)
        # SMTP Sending
        for to_email_addr in to_email_addresses:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = FROM_GMAIL
            msg['To'] = to_email_addr
            msg.attach(MIMEText(email_content, "html"))

            try:
                server = smtplib.SMTP(GMAIL_HOST, GMAIL_PORT)
                server.starttls()
                server.login(FROM_GMAIL, FROM_GMAIL_PASSWORD)
                server.send_message(msg)
                print(f"Email sent successfully to {to_email_addr}")
            except Exception as e:
                print(f"Error sending Email to {to_email_addr}: {e}")
                pass
            finally:
                server.quit()
    except Exception as e:
        print(f"General error sending Email: {e}")
        pass
