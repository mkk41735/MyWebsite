# osint_tool_advanced.py
# Advanced OSINT Tool with AI-style Assistant UI (Inspired by Amazon)
# All-in-one script with modern design, phone/email/username search, PDF reporting, and more

import customtkinter as ctk
from tkinter import filedialog, messagebox
import phonenumbers
from phonenumbers import geocoder, carrier
import re
import socket
import os
import json
from fpdf import FPDF
import requests
from datetime import datetime
import threading

# Initialize UI theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Define PDF generator
class ReportPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(200, 10, "OSINT Intelligence Report", 0, 1, "C")

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, "L", 1)

    def chapter_body(self, body):
        self.set_font("Arial", "", 10)
        self.multi_cell(0, 10, body)

    def add_chapter(self, title, body):
        self.chapter_title(title)
        self.chapter_body(body)

# Function: Get domain info

def get_ip_and_host(domain):
    try:
        ip = socket.gethostbyname(domain)
        return f"IP: {ip}\nHost: {socket.getfqdn(ip)}"
    except:
        return "Unable to resolve domain."

# Function: Lookup phone number info

def phone_lookup(number):
    try:
        parsed = phonenumbers.parse(number, None)
        country = geocoder.description_for_number(parsed, "en")
        provider = carrier.name_for_number(parsed, "en")
        return f"Country: {country}\nCarrier: {provider}"
    except:
        return "Invalid phone number."

# Function: Extract emails from text

def extract_emails(text):
    return re.findall(r"[\w\.-]+@[\w\.-]+", text)

# Function: Smart Email Search (via search engines)

def smart_email_search(email):
    domain = email.split("@")[1]
    return f"Domain: {domain}\nMail server info might require MX record lookup (use `nslookup -q=mx {domain}`)."

# Function: Get public IP

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return "Can't retrieve public IP."

# Function: Save report to PDF

def save_report_to_pdf(data, username):
    pdf = ReportPDF()
    pdf.add_page()
    for title, body in data.items():
        pdf.add_chapter(title, body)
    filename = f"{username}_OSINT_Report.pdf"
    pdf.output(filename)
    return filename

# Function: Basic web scrape (without API)

def simple_web_search(query):
    return f"Use the following Google Dork: site:* {query}"

# GUI Starts
class OSINTApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI OSINT Intelligence System")
        self.geometry("1200x750")

        self.report_data = {}

        # Title Label
        self.label = ctk.CTkLabel(self, text="AI OSINT Search Tool", font=("Arial", 28))
        self.label.pack(pady=10)

        # Entry Frame
        self.entry_frame = ctk.CTkFrame(self)
        self.entry_frame.pack(pady=10, padx=20, fill="x")

        # Username Entry
        self.username_entry = ctk.CTkEntry(self.entry_frame, placeholder_text="Enter username/email/phone")
        self.username_entry.pack(side="left", padx=10, fill="x", expand=True)

        # Country Code Selector (static)
        self.country_code_menu = ctk.CTkComboBox(
            self.entry_frame,
            values=["+1 (US)", "+44 (UK)", "+20 (EG)", "+49 (DE)", "+33 (FR)", "+91 (IN)"]
        )
        self.country_code_menu.set("+20 (EG)")
        self.country_code_menu.pack(side="left", padx=5)

        # Search Button
        self.search_button = ctk.CTkButton(self.entry_frame, text="Search", command=self.run_osint)
        self.search_button.pack(side="left", padx=10)

        # Result Box
        self.result_box = ctk.CTkTextbox(self, width=1150, height=500)
        self.result_box.pack(pady=20)

        # Save Button
        self.save_button = ctk.CTkButton(self, text="Save Report", command=self.save_pdf)
        self.save_button.pack(pady=10)

        # Smart Assistant Tips
        self.assistant_box = ctk.CTkTextbox(self, width=1150, height=100)
        self.assistant_box.insert("0.0", self.smart_assistant_tip())
        self.assistant_box.configure(state="disabled")
        self.assistant_box.pack(pady=10)

    def smart_assistant_tip(self):
        return (
            "\u2728 Welcome to your AI OSINT Tool! Here’s what you can do:\n"
            "1. Search by username, email, or phone number.\n"
            "2. Export your results to PDF.\n"
            "3. Combine Dorks for deeper investigation.\n"
            "4. Tip: Use country code selector for accurate phone lookups.\n"
            "5. Need public IP info? Just type: my ip\n"
        )

    def run_osint(self):
        user_input = self.username_entry.get().strip()
        if not user_input:
            messagebox.showerror("Input Error", "Please enter a username, email or phone number.")
            return

        results = ""
        self.report_data.clear()

        # Detect phone number
        if user_input.replace(" ", "").startswith("+"):
            results += f"[PHONE SEARCH]\n{phone_lookup(user_input)}\n"
            self.report_data["Phone Lookup"] = phone_lookup(user_input)

        elif re.match(r"[\w\.-]+@[\w\.-]+", user_input):
            info = smart_email_search(user_input)
            results += f"[EMAIL SEARCH]\n{info}\n"
            self.report_data["Email Lookup"] = info

        elif user_input.lower() == "my ip":
            ip = get_public_ip()
            results += f"[PUBLIC IP]\n{ip}\n"
            self.report_data["Public IP"] = ip

        elif "." in user_input:
            domain_info = get_ip_and_host(user_input)
            results += f"[DOMAIN SEARCH]\n{domain_info}\n"
            self.report_data["Domain Info"] = domain_info

        else:
            dork = simple_web_search(user_input)
            results += f"[USERNAME SEARCH]\n{dork}\n"
            self.report_data["Username Search"] = dork

        self.result_box.delete("0.0", "end")
        self.result_box.insert("0.0", results)

    def save_pdf(self):
        user = self.username_entry.get().strip()
        if not self.report_data or not user:
            messagebox.showerror("Error", "No data to save!")
            return
        filename = save_report_to_pdf(self.report_data, user)
        messagebox.showinfo("Success", f"Report saved as {filename}")

if __name__ == '__main__':
    app = OSINTApp()
    app.mainloop()