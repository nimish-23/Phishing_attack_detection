from imapclient import IMAPClient
import email
import time

# Import processor
from receive_mail import handle_email  


def ensure_folder(client, folder_name):
    folders = [f[2] for f in client.list_folders()]
    if folder_name not in folders:
        client.create_folder(folder_name)


def start_idle_listener(user_email=None, password=None, stop_event=None, log_callback=None):
    """
    Start the IMAP IDLE listener.

    Args:
        user_email: Gmail address to monitor
        password: Gmail app password
        stop_event: threading.Event — set this to stop the listener gracefully
        log_callback: optional callable(level, message) to capture logs
    """
    HOST = "imap.gmail.com"

    def log(level, message):
        """Send log to callback if available, and always print."""
        print(message)
        if log_callback:
            log_callback(level, message)

    if not user_email or not password:
        log("error", "[ERROR] Email and password are required.")
        return

    try:
        log("info", f"[SYSTEM] Connecting to {HOST}:993 (SSL)...")

        with IMAPClient(HOST, ssl=True) as client:
            client.login(user_email, password)
            log("success", f"[SUCCESS] Authenticated as {user_email}")

            client.select_folder("INBOX")
            log("info", "[SYSTEM] INBOX selected")

            ensure_folder(client, "Phishing")
            log("success", "[SUCCESS] Phishing quarantine folder verified [OK]")

            log("success", "[LISTENING] Waiting for new emails...\n")

            last_seen_id = None

            while True:
                # Check if we should stop
                if stop_event and stop_event.is_set():
                    log("warn", "[SYSTEM] Stop signal received — shutting down gracefully")
                    break

                try:
                    # Start IDLE mode
                    client.idle()
                    responses = client.idle_check(timeout=5)

                    triggered = False

                    for response in responses:
                        if b'EXISTS' in response:
                            log("info", "[NEW] New email detected!")
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
                        log("info", f"[FETCH] UID: {latest_id}")

                        raw_message = client.fetch([latest_id], ['RFC822'])
                        msg = email.message_from_bytes(
                            raw_message[latest_id][b'RFC822']
                        )

                        # Send to processor (wrapped to prevent one bad email from crashing the loop)
                        try:
                            handle_email(client, latest_id, msg, log_callback=log)
                        except Exception as proc_err:
                            log("error", f"[ERROR] Failed to process UID {latest_id}: {proc_err}")
                        
                        # Always update so we don't re-process the same email
                        last_seen_id = latest_id

                except Exception as e:
                    log("error", f"[ERROR] {e}")
                    time.sleep(5)

    except Exception as e:
        log("error", f"[ERROR] Connection failed: {e}")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    EMAIL = os.getenv("GMAIL_EMAIL")
    PASSWORD = os.getenv("GMAIL_PASS_KEY")

    if not EMAIL or not PASSWORD:
        print("[ERROR] Set GMAIL_EMAIL and GMAIL_PASS_KEY in your .env file")
        exit(1)

    print("[SYSTEM] Starting Phishing Detection Backend...")
    try:
        start_idle_listener(user_email=EMAIL, password=PASSWORD)
    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutting down gracefully...")