import email
import json
import re
from bs4 import BeautifulSoup
from email.header import decode_header
from urllib.parse import urlparse
from collections import Counter

# SAFETY MODE
DRY_RUN = False


# ================= HELPERS =================

def normalize_domain(domain):
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain


def get_domain(url):
    try:
        domain = urlparse(url).netloc.lower()
        return domain.replace("www.", "")
    except:
        return ""


def decode_text(text):
    if not text:
        return ""

    parts = decode_header(text)
    result = ""

    for part, encoding in parts:
        if isinstance(part, bytes):
            result += part.decode(encoding or "utf-8", errors="ignore")
        else:
            result += part

    return result


def clean_text(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'http\S+', '', text)
    return text.strip()


def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ")


def extract_links_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return [a["href"] for a in soup.find_all("a", href=True)]


# ================= BODY EXTRACTION =================

def get_body_and_links(msg):
    text = ""
    links = []
    has_html = False

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" in content_disposition:
                continue

            payload = part.get_payload(decode=True)
            if not payload:
                continue

            if len(payload) > 300000:
                continue

            payload = payload.decode(errors="ignore")

            if content_type == "text/plain":
                text += payload

            elif content_type == "text/html":
                has_html = True
                text += clean_html(payload)
                links.extend(extract_links_from_html(payload))

    else:
        payload = msg.get_payload(decode=True)
        if payload:
            payload = payload.decode(errors="ignore")
            text += payload

    return text, links, has_html


# ================= MAIN PROCESSOR =================

def process_email(msg):
    subject = decode_text(msg["subject"])
    sender = decode_text(msg["from"])

    body, links, has_html = get_body_and_links(msg)
    body = clean_text(body)

    unique_links = list(set(
        link for link in links
        if link and link != "#" and link.startswith("http")
    ))

    normalized_domains = [
        normalize_domain(get_domain(l)) for l in unique_links
    ]

    domains = list(set(normalized_domains))
    domain_counts = Counter(normalized_domains)

    return {
        "metadata": {
            "sender": sender,
            "subject": subject,
            "message_id": msg.get("Message-ID"),
            "date": msg.get("Date")
        },
        "content": {
            "text": body[:1000],
            "length": len(body),
            "has_html": has_html
        },
        "links": {
            "count": len(unique_links),
            "items": [
                {"url": l, "domain": normalize_domain(get_domain(l))}
                for l in unique_links[:20]
            ],
            "domains": domains,
            "domain_counts": dict(domain_counts)
        }
    }


# ================= ACTION =================

def move_to_phishing(client, uid):
    if DRY_RUN:
        print(f"[DRY RUN] Would move UID {uid} to Phishing")
        return

    def perform_move():
        try:
            client.move(uid, "Phishing")
            print(f"[SUCCESS] Moved UID {uid} to Phishing folder.")
            return True
        except:
            try:
                client.copy(uid, "Phishing")
                client.delete_messages(uid)
                client.expunge()
                print(f"[SUCCESS] Copied UID {uid} to Phishing folder and deleted original.")
                return True
            except Exception as e:
                return e

    result = perform_move()
    if result is not True:
        print(f"[WARN] Phishing folder missing. Creating it now...")
        try:
            client.create_folder("Phishing")
            print(f"[SUCCESS] Phishing folder successfully created.")
            
            # Retry move
            retry_result = perform_move()
            if retry_result is not True:
                 print(f"[ERROR] Could not move email even after creating folder: {retry_result}")
        except Exception as create_err:
            print(f"[ERROR] Failed to create Phishing folder dynamically: {create_err}")


# ================= SCORING MODEL =================

def get_phishing_score(email_data):
    """
    Placeholder for future AI/ML phishing detection model.
    Analyzes email structure and returns a confidence score (0.0 to 1.0).
    """
    # TODO: Integrate your real ML/AI model here.
    return 0.0  # Returns dummy 0.0 safe score by default


# ================= MAIN HANDLER =================

def handle_email(client, uid, msg):
    print("\n[PROCESSING] Processing email...")

    email_data = process_email(msg)

    subject = email_data["metadata"]["subject"]
    sender = email_data["metadata"]["sender"]

    print(f"UID: {uid}")
    print(f"Subject: {subject}")
    print(f"Sender: {sender}")

    # 1. Simple keyword override for testing
    is_test_phishing = "phishing" in subject.lower()

    # 2. ML Scoring Decision
    confidence_score = get_phishing_score(email_data)
    print(f"Phishing Confidence Score: {confidence_score:.2f}")

    # DECISION EVALUATION
    if is_test_phishing:
        print("[MATCH] Keyword override found -> moving to Phishing")
        move_to_phishing(client, uid)
    elif confidence_score > 0.75:
        print("[HIGH RISK] Score > 0.75 -> moving to Phishing")
        move_to_phishing(client, uid)
    else:
        print("[SAFE] Email is safe (No keyword & Score <= 0.75)")

    print("\n[DATA]")
    print("=" * 60)
    print(json.dumps(email_data, indent=4))
    print("=" * 60)