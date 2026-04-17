# Phishing Attack Detection System

> ⚠️ **PROTOTYPE PHASE** ⚠️  
> *This project is currently under active development. The pipeline is functional, but Machine Learning scoring integration and the frontend Web UI are placeholders/WIP.*

A real-time email defense system that monitors your inbox, evaluates incoming emails for phishing threats using a Machine Learning pipeline, and automatically quarantines detected attacks.

## 🚀 How it Works

The system runs completely in the background via a persistent IMAP connection. Its lifecycle consists of:
1. **Live Monitoring (`listener`)**: Stays connected to your Gmail account in zero-overhead IDLE mode, instantly detecting when a new email hits your inbox.
2. **Extraction (`processor`)**: Scrapes the incoming email to retrieve sender metadata, cleanses the text body, and parses all URLs/domains inside the email.
3. **Evaluation (`ML scoring`)**: Passes the sanitized payload into a Machine Learning confidence scoring function to evaluate phishing risk. 
4. **Quarantine (`action`)**: If the overall confidence score exceeds 75% or triggers manual test flags, it automatically intercepts the email and removes it from your main inbox, safely quarantining it in a dedicated "Phishing" folder on your mail server.

## 📁 Project Structure

```text
Phishing_attack_detection/
├── backend/
│   ├── main.py                # App entrypoint & continuous launcher
│   └── service/
│       ├── listener.py        # Real-time event monitor (IMAP IDLE)
│       ├── receive_mail.py    # Payload extraction, AI decision logic, and Quarantine execution
│       └── q_email.py         # Testing script (run a batch check manually)
├── frontend/                  # Future Web UI integration
├── .gitignore
└── .env                       # Secrets (Requires valid credentials!)
```

## ⚙️ Setup & Installation

**1. Create a `.env` file** in the root directory and add the following keys for authentication:
```ini
GMAIL_PASS_KEY="your-google-app-password-here"
```
*(Because this script bypasses traditional web login, you must generate an "App Password" from your Google Account Security Dashboard).*

**2. Activate your Virtual Environment:**
```bash
# Windows
.\venv\Scripts\activate
```

**3. Install Dependencies:**  
Make sure you have installed the required libraries locally:
```bash
pip install imapclient beautifulsoup4 python-dotenv
```

## ▶️ Running the Application

To start the real-time background protection, navigate to the `backend` folder and run the `main.py` entrypoint:

```bash
cd backend
python main.py
```
This will establish an incredibly lightweight, continuous connection to your inbox. Use `Ctrl+C` to gracefully shut down the listener.

## 🧪 Current Testing Workflows

The current detection logic has two streams you can use during testing:
- **ML Scoring Function Prototype**: Ready to accept your trained model scoring (defaults to 0.0).
- **Manual Flagging**: A simple text override that trips an alarm if the exact word `"phishing"` is placed in an email's subject line.