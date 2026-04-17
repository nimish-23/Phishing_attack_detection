from imapclient import IMAPClient
import email
import time
from dotenv import load_dotenv
import os

# Import processor
from receive_mail import handle_email  

load_dotenv()

HOST = "imap.gmail.com"
EMAIL = "nimishsinkar2004@gmail.com"
PASSWORD = os.getenv("GMAIL_PASS_KEY")


def ensure_folder(client, folder_name):
    folders = [f[2] for f in client.list_folders()]
    if folder_name not in folders:
        client.create_folder(folder_name)


def start_idle_listener():
    with IMAPClient(HOST, ssl=True) as client:
        client.login(EMAIL, PASSWORD)
        client.select_folder("INBOX")

        ensure_folder(client, "Phishing")

        print("[LISTENING] Waiting for new emails...\n")

        last_seen_id = None

        while True:
            try:
                # Start IDLE mode
                client.idle()
                responses = client.idle_check(timeout=5)

                triggered = False

                for response in responses:
                    if b'EXISTS' in response:
                        print("[NEW] New email detected!")
                        triggered = True

                client.idle_done()

                # Fallback check
                uids = client.search(['ALL'])
                if not uids:
                    continue

                latest_id = uids[-1]

                if last_seen_id is None:
                    last_seen_id = latest_id

                elif latest_id != last_seen_id:
                    print(f"[FETCH] UID: {latest_id}")

                    raw_message = client.fetch([latest_id], ['RFC822'])
                    msg = email.message_from_bytes(
                        raw_message[latest_id][b'RFC822']
                    )

                    # Send to processor
                    handle_email(client, latest_id, msg)
                    
                    # Update after successful processing to avoid skipping on failure
                    last_seen_id = latest_id

            except Exception as e:
                print("[ERROR]", e)
                time.sleep(5)


if __name__ == "__main__":
    start_idle_listener()