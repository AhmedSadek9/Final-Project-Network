import smtplib
import imaplib
import email
import socket
import time
import threading
import csv
import os
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, scrolledtext
from plyer import notification
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header

# Mail Server Configuration 
SMTP_SERVER, SMTP_PORT = "smtp.ethereal.email", 587
IMAP_SERVER, IMAP_PORT = "imap.ethereal.email", 993
NOTIFICATION_HOST, NOTIFICATION_PORT = "127.0.0.1", 9999

class EmailApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CDS Email Client - Professional Edition")
        self.root.geometry("500x850")
        self.root.configure(padx=20, pady=20)
        
        self.attachment_path = ""
        self.perf_data = [] # To store latency for the final report
        
        self.create_widgets()

    def create_widgets(self):
        #  Authentication
        tk.Label(self.root, text="Authentication", font=('Helvetica', 12, 'bold'), fg="#333").pack(anchor="w")
        
        self.entries = {}
        for label in ["Sender Email:", "Password:"]:
            tk.Label(self.root, text=label).pack(anchor="w")
            entry = tk.Entry(self.root, width=60, show="*" if "Password" in label else "")
            entry.pack(pady=2, ipady=3)
            self.entries[label] = entry

        # Message Details
        ttk.Separator(self.root, orient='horizontal').pack(fill='x', pady=10)
        tk.Label(self.root, text="Message Details", font=('Helvetica', 12, 'bold'), fg="#333").pack(anchor="w")

        for label in ["Recipient:", "Subject:"]:
            tk.Label(self.root, text=label).pack(anchor="w")
            entry = tk.Entry(self.root, width=60)
            entry.pack(pady=2, ipady=3)
            self.entries[label] = entry

        tk.Label(self.root, text="Body:").pack(anchor="w")
        self.body_text = tk.Text(self.root, height=5, width=60)
        self.body_text.pack(pady=2)

        # Attachment Button
        self.btn_attach = tk.Button(self.root, text=" Attach File", command=self.select_file)
        self.btn_attach.pack(pady=5)
        self.lbl_file = tk.Label(self.root, text="No file attached", fg="gray", font=('Helvetica', 8))
        self.lbl_file.pack()

        # Operations
        self.send_btn = tk.Button(self.root, text="📤 Send SMTP & Notify", bg="#28a745", fg="white", 
                                  font=('Helvetica', 10, 'bold'), command=lambda: self.run_thread(self.send_email))
        self.send_btn.pack(fill="x", pady=5)

        self.fetch_btn = tk.Button(self.root, text="📥 Fetch IMAP & Notify", bg="#007bff", fg="white", 
                                   font=('Helvetica', 10, 'bold'), command=lambda: self.run_thread(self.fetch_email))
        self.fetch_btn.pack(fill="x", pady=5)

        # Performance Reporting
        self.report_btn = tk.Button(self.root, text=" Export Performance CSV", bg="#6c757d", fg="white", 
                                    command=self.export_report)
        self.report_btn.pack(fill="x", pady=5)

        # Network Activity Log 
        tk.Label(self.root, text="Network Activity Log:", font=('Helvetica', 10, 'bold')).pack(anchor="w", pady=(10,0))
        self.log_area = scrolledtext.ScrolledText(self.root, height=10, width=60, state='disabled', bg="#f8f9fa")
        self.log_area.pack(pady=5)

    def select_file(self):
        self.attachment_path = filedialog.askopenfilename()
        if self.attachment_path:
            self.lbl_file.config(text=f"Attached: {os.path.basename(self.attachment_path)}", fg="blue")

    def write_log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def run_thread(self, target):
        """Runs network tasks in a background thread to keep the GUI responsive."""
        threading.Thread(target=target, daemon=True).start()

    def send_tcp_notification(self, message):
        """Communicates with the local TCP Notification Server"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((NOTIFICATION_HOST, NOTIFICATION_PORT))
                s.sendall(message.encode("utf-8"))
                self.write_log(f"TCP Notification sent: '{message}'")
        except Exception as e:
            self.write_log(f"Notification Server Error: {e}")

    def send_email(self):
        start_time = time.time()
        self.write_log(f"Connecting to SMTP server at {SMTP_SERVER}...")
        
        try:
            sender = self.entries["Sender Email:"].get()
            password = self.entries["Password:"].get()
            receiver = self.entries["Recipient:"].get()
            subject = self.entries["Subject:"].get()
            body = self.body_text.get("1.0", tk.END)

            msg = MIMEMultipart()
            msg["From"], msg["To"], msg["Subject"] = sender, receiver, subject
            msg.attach(MIMEText(body, "plain"))

            # Attachment logic
            if self.attachment_path:
                with open(self.attachment_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(self.attachment_path)}")
                msg.attach(part)

            # SMTP Protocol Sequence
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls() # Secure the connection
                server.login(sender, password)
                server.sendmail(sender, receiver, msg.as_string())
            
            latency = time.time() - start_time
            self.write_log(f"SMTP Success. Latency: {latency:.4f}s")
            self.perf_data.append(["SMTP Send", f"{latency:.4f}", time.strftime('%H:%M:%S')])
            self.send_tcp_notification("Email Sent Successfully")
            messagebox.showinfo("Success", f"Email Sent!\nLatency: {latency:.4f}s")

        except Exception as e:
            self.write_log(f"SMTP Error: {e}")
            self.send_tcp_notification("Email Sending Failed")
            messagebox.showerror("Error", f"SMTP Failed: {e}")

    def fetch_email(self):
        start_time = time.time()
        self.write_log(f"Connecting to IMAP server at {IMAP_SERVER}...")
        
        try:
            email_addr = self.entries["Sender Email:"].get()
            password = self.entries["Password:"].get()
            
            with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as mail:
                mail.login(email_addr, password)
                mail.select("inbox")
                _, data = mail.search(None, "ALL")
                
                if data[0]:
                    latest_id = data[0].split()[-1]
                    _, msg_data = mail.fetch(latest_id, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    subj = decode_header(msg["Subject"])[0][0]
                    if isinstance(subj, bytes): subj = subj.decode()
                    
                    # Desktop Push Notification
                    notification.notify(
                        title="IMAP Client Alert", 
                        message=f"New Mail Received: {subj}", 
                        timeout=5
                    )
                    
                    latency = time.time() - start_time
                    self.write_log(f"IMAP Success. Latency: {latency:.4f}s")
                    self.perf_data.append(["IMAP Fetch", f"{latency:.4f}", time.strftime('%H:%M:%S')])
                    self.send_tcp_notification("Email Received Successfully")
                    messagebox.showinfo("IMAP Result", f"Latest Email Subject: {subj}\nLatency: {latency:.4f}s")
                else:
                    self.write_log("Inbox is empty.")
                    messagebox.showinfo("IMAP Info", "The inbox is currently empty.")
                
        except Exception as e:
            self.write_log(f"IMAP Error: {e}")
            self.send_tcp_notification("Email Receiving Failed")
            messagebox.showerror("Error", f"IMAP Failed: {e}")

    def export_report(self):
        """Saves performance data to CSV for network analysis reports"""
        if not self.perf_data:
            messagebox.showwarning("Warning", "No performance data available to export!")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", 
            filetypes=[("CSV files", "*.csv")],
            title="Save Performance Report"
        )
        if file_path:
            with open(file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Operation", "Latency (s)", "Timestamp"])
                writer.writerows(self.perf_data)
            messagebox.showinfo("Export Success", f"Report saved to:\n{file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = EmailApp(root)
    root.mainloop()
    
    
    # python email_client_GUI.py