from notifypy import Notify
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json

from dotenv import load_dotenv
import os


# Load environment variables from the .env file
load_dotenv()

DIRNAME = os.path.dirname(os.path.abspath(__file__)).replace("\\mailer", "")
AVAILABLE_PATH = f'{DIRNAME}/results/available.json'
SENT_PATH = f'{DIRNAME}/results/sent-{datetime.today().strftime("%d-%m")}.json'


def read_data_file(file_path):
    file = open(file_path, 'r', encoding='utf-8')
    data = json.load(file)
    file.close()
    return data

configs = read_data_file(f'{DIRNAME}/configs.json')



SMTP_HOST = configs['SMTP_HOST']
SMTP_PORT = configs['SMTP_PORT']
NOTIFICATION_EMAIL = configs['NOTIFICATION_EMAIL']


def write_data_file(file_path, data):
    # Open the file in write mode
    file = open(file_path, 'w', encoding='utf-8')

    # Write the data as JSON
    json.dump(data, file)

    # Close the file
    file.close()


def generate_email_body(data):
    # Start building the HTML string
    html = """
    <html>
    <head>
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th, td {
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h2>Residences Information</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Address</th>
                <th>Price (From)</th>
                <th>Price (To)</th>
                <th>Link</th>
            </tr>"""

    data = [d for d in data if 'from_price' in d and 'to_price' in d]

    if len(data) == 0:
        return None

    # Iterate over each residence entry and create a table row
    for residence in data:
        html += f"""
        <tr>
            <td>{residence['name']}</td>
            <td>{residence['address']}</td>
            <td>{residence['from_price']} €/mois</td>
            <td>{residence['to_price']} €/mois</td>
            <td><a href="{residence['link']}" target="_blank">Visit Residence</a></td>
        </tr>"""

    # Close the HTML tags
    html += """
        </table>
    </body>
    </html>"""

    return html


def setup_the_server(address, password):
    # Set up the server
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()  # Use TLS (Transport Layer Security)
    server.login(address, password)

    return server


def setup_the_mime(from_address, to_address):
    data = read_data_file(AVAILABLE_PATH)
    html_body = generate_email_body(data)

    if html_body is None:
        return None, None

    # Get today's date
    today = datetime.today()

    # Format the date as DD/MM
    formatted_date = today.strftime("%d/%m")

    subject = f'ARPEJ\'s Available Residences - {formatted_date}'

    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = f"\"ARPEJ SCRAPER\"<{from_address}>"
    message['To'] = to_address
    message['Subject'] = subject
    message.attach(MIMEText(html_body, 'html'))

    return message, data


def send_email():
    # Your Outlook account credentials
    outlook_address = os.getenv('ARPEJ_SCRAPER_EMAIL')
    outlook_password = os.getenv('ARPEJ_SCRAPER_PASSWORD')

    if outlook_address is None or outlook_password is None:
        print(
            "Please set the ARPEJ_SCRAPER_EMAIL and ARPEJ_SCRAPER_PASSWORD in the .env file.")
        return

    # Email details
    to_address = NOTIFICATION_EMAIL

    message, residences = setup_the_mime(outlook_address, to_address)

    if message == None:
        print("No residences available. Email not sent.")
        return

    try:
        server = setup_the_server(outlook_address, outlook_password)

        # Send the email
        text = message.as_string()
        server.sendmail(outlook_address, to_address, text)
        print("Email sent successfully.")

        notification = Notify()
        notification.title = f"New Residence{'' if len(residences) == 1 else 's'} Available"
        notification.message = ", ".join(
            [residence['name'].capitalize() for residence in residences[:3]]) + ("..." if len(residences) > 3 else "")
        notification.application_name = "ARPEJ SCRAPER"
        notification.icon = f'{DIRNAME}/resources/arpej-logo.png'

        notification.send()

        available = read_data_file(AVAILABLE_PATH)
        sent = read_data_file(SENT_PATH)

        for residence in available:
            sent.append(residence)

        write_data_file(SENT_PATH, sent)

    except Exception as e:
        print(f"Failed to send email. Error: {e}")

    finally:
        server.quit()
