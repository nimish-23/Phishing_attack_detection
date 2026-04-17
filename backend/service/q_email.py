import os
import email
from imapclient import IMAPClient
from dotenv import load_dotenv

from receive_mail import handle_email

load_dotenv()

HOST = "imap.gmail.com"
EMAIL = "nimishsinkar2004@gmail.com"
PASSWORD = os.getenv("GMAIL_PASS_KEY")

def ensure_folder(client, folder_name):
    folders = [f[2] for f in client.list_folders()]
    if folder_name not in folders:
        client.create_folder(folder_name)

with IMAPClient(HOST, ssl=True) as client:
    client.login(EMAIL, PASSWORD)
    client.select_folder("INBOX")

    ensure_folder(client, "Phishing")

    # ✅ limit emails for safety
    uids = client.search(['UNSEEN'])[:5]

    if not uids:
        print("No new emails")
    else:
        messages = client.fetch(uids, ['RFC822'])

        for uid, msg_data in messages.items():
            raw_email = msg_data[b'RFC822']

            # 📩 parse email
            msg = email.message_from_bytes(raw_email)

            print(f"\n[FETCHED] UID {uid}")

            # 🔥 PASS TO SECOND FILE (MAIN CHANGE)
            handle_email(client, uid, msg)