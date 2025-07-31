
import time
import json
import smtplib
import io
from pathlib import Path
from email.message import EmailMessage
from datetime import datetime, timedelta
from pymongo import MongoClient
from collections import Counter
import numpy as np

# --- PDF, Plotting, and Data Libraries ---
# Make sure to install them: pip install matplotlib reportlab pandas
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --- Configuration ---
# MONGO_URI = "mongodb+srv://user1:pass1@cluster0.ueflwgp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_URI="mongodb+srv://mandhalakarthikreddy:UY0ka5VMDsXKXX74@cluster0.9idd88a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
BASE_DIR = Path(__file__).resolve().parent
SOFTWARE_ALERT_HISTORY = BASE_DIR / "software_alerts_history.json"
HARDWARE_ALERT_HISTORY = BASE_DIR / "hardware_alerts_history.json"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True) # Create a directory to store reports

# --- Utility Functions ---

def load_json(file_path):
    """Loads JSON data from a file, handling potential errors."""
    if file_path.exists() and file_path.stat().st_size > 0:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[WARN] Corrupt JSON at {file_path}. Treating as empty.")
    return {}

# --- Core Logic ---

def get_new_alerts_for_bank(bank_name, last_check_time):
    """
    Fetches new alerts from local JSON files based on the last check time.
    All times are handled as naive local time.
    """
    software_history = load_json(SOFTWARE_ALERT_HISTORY)
    hardware_history = load_json(HARDWARE_ALERT_HISTORY)
    combined_alerts = {"software": [], "hardware": []}

    # Process software alerts
    for alert in software_history.get(bank_name, []):
        try:
            alert_time = datetime.strptime(alert['timestamp'], "%Y-%m-%d %H:%M:%S")
            if alert_time >= last_check_time:
                combined_alerts["software"].append(alert)
        except (ValueError, KeyError):
            print(f"[WARN] Skipping malformed software alert: {alert}")

    # Process hardware alerts
    for alert in hardware_history.get(bank_name, []):
        try:
            alert_time = datetime.strptime(alert['timestamp'], "%Y-%m-%d %H:%M:%S")
            if alert_time >= last_check_time:
                combined_alerts["hardware"].append(alert)
        except (ValueError, KeyError):
            print(f"[WARN] Skipping malformed hardware alert: {alert}")
            
    return combined_alerts

def create_pdf_report(bank_name, combined_alerts):
    """
    Generates an enhanced PDF report with a multi-level summary and improved visuals.
    """
    report_path = REPORTS_DIR / f"Report_{bank_name}_{datetime.now():%Y-%m-%d_%H%M%S}.pdf"
    doc = SimpleDocTemplate(str(report_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # --- Title ---
    title = Paragraph(f"System Status Report for {bank_name}", styles['h1'])
    timestamp = Paragraph(f"Generated on: {datetime.now():%Y-%m-%d %H:%M:%S}", styles['Normal'])
    story.extend([title, timestamp, Spacer(1, 24)])

    all_alerts = combined_alerts["software"] + combined_alerts["hardware"]
    if not all_alerts:
        story.append(Paragraph("No new alerts to report.", styles['Normal']))
        doc.build(story)
        return report_path

    # --- Sort data for consistency ---
    combined_alerts["software"].sort(key=lambda x: (x.get('software', ''), x.get('system', '')))
    combined_alerts["hardware"].sort(key=lambda x: x.get('atm', ''))

    # --- NEW ORDER: Section 1: Detailed Alert Tables ---
    
    # --- NEW ORDER: Section 2: Overall Summary ---
    story.append(Paragraph("Overall Summary", styles['h2']))
    
    # Chart 1: Overall Alerts by Status (Bar Chart)
    status_counts = Counter(alert['status'] for alert in all_alerts)
    if status_counts:
        fig, ax = plt.subplots(figsize=(5, 3))
        bars = ax.bar(status_counts.keys(), status_counts.values(), color=['red', 'orange'])
        ax.set_title('Total Alerts by Status')
        ax.set_ylabel('Count')
        # NEW: Add labels on bars
        ax.bar_label(bars)
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close(fig)
        img_buffer.seek(0)
        overall_status_chart = Image(img_buffer, width=3*inch, height=1.8*inch)
    
    # Chart 2: Overall Alerts by Source (Pie Chart)
    software_source_counts = Counter(alert['system'] for alert in combined_alerts["software"])
    hardware_source_counts = Counter(alert['atm'] for alert in combined_alerts["hardware"])
    all_sources = software_source_counts + hardware_source_counts
    if all_sources:
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.pie(all_sources.values(), labels=all_sources.keys(), autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        ax.set_title('Alerts by Source (System/ATM)')
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close(fig)
        img_buffer.seek(0)
        pie_chart_img = Image(img_buffer, width=3*inch, height=1.8*inch)

    story.append(Table([[overall_status_chart, pie_chart_img]], colWidths=[3.5*inch, 3.5*inch]))
    story.append(Spacer(1, 24))

    # --- NEW ORDER: Section 3: Detailed Visual Summary ---
    story.append(Paragraph("Detailed Visual Summary", styles['h2']))
    
    # Chart 3: Hardware Alerts by Status (Grouped Bar Chart)
    if combined_alerts["hardware"]:
        df_hw = pd.DataFrame(combined_alerts["hardware"])
        hw_counts = df_hw.groupby(['atm', 'status']).size().unstack(fill_value=0)
        if not hw_counts.empty:
            ax = hw_counts.plot(kind='bar', figsize=(8, 4), color={'Critical': 'red', 'Warning': 'orange'}, rot=0, width=0.8)
            ax.set_title('Hardware Alert Counts by ATM')
            ax.set_xlabel('ATM ID'); ax.set_ylabel('Number of Alerts'); ax.legend(title='Status')
            # NEW: Add labels on grouped bars
            for container in ax.containers:
                ax.bar_label(container)
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=120); plt.close(); img_buffer.seek(0)
            story.append(Image(img_buffer, width=6*inch, height=3*inch))
            story.append(Spacer(1, 12))

    # Chart 4: Software Alerts by Software Name (Grouped Bar Chart)
    if combined_alerts["software"]:
        df_sw = pd.DataFrame(combined_alerts["software"])
        sw_counts = df_sw.groupby(['software', 'status']).size().unstack(fill_value=0)
        if not sw_counts.empty:
            ax = sw_counts.plot(kind='bar', figsize=(8, 4), color={'Critical': 'red', 'Warning': 'orange'}, rot=45, width=0.8)
            ax.set_title('Alert Counts by Software Name')
            ax.set_xlabel('Software'); ax.set_ylabel('Number of Alerts'); ax.legend(title='Status')
            for container in ax.containers:
                ax.bar_label(container)
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=120); plt.close(); img_buffer.seek(0)
            story.append(Image(img_buffer, width=6*inch, height=3*inch))
            story.append(Spacer(1, 12))

    # Chart 5: Software Alerts by System (Grouped Bar Chart)
    if combined_alerts["software"]:
        df_sw = pd.DataFrame(combined_alerts["software"])
        sys_counts = df_sw.groupby(['system', 'status']).size().unstack(fill_value=0)
        if not sys_counts.empty:
            ax = sys_counts.plot(kind='bar', figsize=(10, 5), color={'Critical': 'red', 'Warning': 'orange'}, rot=45, width=0.8)
            ax.set_title('Alert Counts by System Component')
            ax.set_xlabel('System Component'); ax.set_ylabel('Number of Alerts'); ax.legend(title='Status')
            for container in ax.containers:
                ax.bar_label(container)
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=120); plt.close(); img_buffer.seek(0)
            story.append(Image(img_buffer, width=7*inch, height=3.5*inch))
            story.append(Spacer(1, 24))

    story.append(Paragraph("Detailed Alerts", styles['h2']))
    
    # Software Alerts Table
    if combined_alerts["software"]:
        story.append(Paragraph("Software Alerts", styles['h3']))
        data = [["System", "Software", "Status", "Timestamp"]]
        table_style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkslategray), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]
        for i, alert in enumerate(combined_alerts["software"]):
            row_num = i + 1
            data.append([alert.get('system'), alert.get('software'), alert.get('status'), alert.get('timestamp')])
            if alert.get('status') == 'Critical':
                table_style_commands.append(('BACKGROUND', (0, row_num), (-1, row_num), colors.lightcoral))
            elif alert.get('status') == 'Warning':
                table_style_commands.append(('BACKGROUND', (0, row_num), (-1, row_num), colors.lightyellow))
        table = Table(data, colWidths=[2*inch, 1.5*inch, 1*inch, 2*inch])
        table.setStyle(TableStyle(table_style_commands))
        story.append(table)
        story.append(Spacer(1, 12))

    # Hardware Alerts Table
    if combined_alerts["hardware"]:
        story.append(Paragraph("Hardware Alerts", styles['h3']))
        data = [["ATM", "Status", "Timestamp"]]
        table_style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkslategray), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]
        for i, alert in enumerate(combined_alerts["hardware"]):
            row_num = i + 1
            data.append([alert.get('atm'), alert.get('status'), alert.get('timestamp')])
            if alert.get('status') == 'Critical':
                table_style_commands.append(('BACKGROUND', (0, row_num), (-1, row_num), colors.lightcoral))
            elif alert.get('status') == 'Warning':
                table_style_commands.append(('BACKGROUND', (0, row_num), (-1, row_num), colors.lightyellow))
        table = Table(data, colWidths=[2.5*inch, 1*inch, 3*inch])
        table.setStyle(TableStyle(table_style_commands))
        story.append(table)
    
    story.append(Spacer(1, 24))

    doc.build(story)
    return report_path
def send_consolidated_mail(user_email, bank_name, combined_alerts):
    """Sends a consolidated email with a PDF report attached."""
    sender_email = "mandhalakarthikreddy@gmail.com"
    app_password = "yiwa asck mnpi oths"

    report_path = create_pdf_report(bank_name, combined_alerts)

    msg = EmailMessage()
    msg['Subject'] = f"System Status Report for {bank_name}"
    msg['From'] = sender_email
    msg['To'] = user_email
    msg.set_content(f"Hello,\n\nPlease find the attached system status report for {bank_name}.\n\nBest regards,\nJatayu Banking Prediction Team")

    with open(report_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=report_path.name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
            print(f"✅ PDF report sent successfully to {user_email}")
    except Exception as e:
        print(f"❌ Error sending PDF report to {user_email}: {e}")
    finally:
        report_path.unlink() # Clean up the generated report file

def notification_dispatcher():
    """Main loop to check for users and dispatch notifications."""
    print("🚀 Consolidated Notification Dispatcher (Local Time) Started...")
    while True:
        try:
            now_local = datetime.now()
            all_users = list(users_collection.find())

            for user in all_users:
                user_email = user.get("email")
                bank_name = user.get("bank")

                if not user_email or not bank_name:
                    continue

                try:
                    user_timer_minutes = int(user.get("timer", 4))
                except ValueError:
                    # print("Only if string is integer is converted else not")
                    print(f"mail alerts for {user_email} for {bank_name} have been stopped succesfully...")
                    continue
                except Exception as e:
                    print("An error occurred ",e)
                    continue
                last_notified = user.get("last_notified_at", now_local - timedelta(days=1))
                
                if not isinstance(last_notified, datetime):
                    last_notified = now_local - timedelta(days=1)

                next_due_time = last_notified + timedelta(minutes=user_timer_minutes)

                if now_local >= next_due_time:
                    print(f"⏰ Time to notify {user_email} for {bank_name} (Timer: {user_timer_minutes} mins)...")
                    
                    alerts_to_send = get_new_alerts_for_bank(bank_name, last_notified)

                    if alerts_to_send["software"] or alerts_to_send["hardware"]:
                        send_consolidated_mail(user_email, bank_name, alerts_to_send)
                        users_collection.update_one({"_id": user["_id"]}, {"$set": {"last_notified_at": now_local}})
                    else:
                        print(f"  -> No new alerts for {bank_name}. Skipping.")

        except Exception as e:
            print(f"[ERROR] An unexpected error occurred in the dispatcher loop: {e}")

        time.sleep(60)

if __name__ == "__main__":
    try:
        client = MongoClient(MONGO_URI)
        db = client["user_db"]
        users_collection = db["users"]
        client.server_info()
        print("✅ MongoDB connection successful.")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        exit()

    notification_dispatcher()
