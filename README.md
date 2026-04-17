# Phishing Attack Detection System

**Note: Prototype Phase**
This project is currently under active development. The core pipeline is functional, but the machine learning scoring integration and the web-based user interface remain as placeholders pending completion.

## System Overview

This application provides real-time email monitoring and automated quarantine routing. The system evaluates incoming emails for phishing threats and isolates flagged messages.

### Pipeline Architecture

1. **Listener:** Maintains a continuous IMAP IDLE connection to monitor a designated inbox for incoming messages.
2. **Processor:** Extracts sender metadata, sanitizes the message body, and parses embedded URLs and domains.
3. **Scoring Engine:** Feeds sanitized email data into a scoring function to determine the probability of a phishing attack.
4. **Quarantine Execution:** Automatically routes emails that exceed the target confidence threshold (or trigger manual evaluation flags) to a designated isolation folder on the mail server.

## Project Structure

```text
Phishing_attack_detection/
├── backend/
│   ├── main.py                # Main application entry point
│   └── service/
│       ├── listener.py        # IMAP IDLE event monitor
│       ├── receive_mail.py    # Payload extraction and quarantine logic
│       └── q_email.py         # Batch testing script
├── frontend/                  # Web UI directory (pending implementation)
├── .gitignore
├── requirements.txt
└── .env.example               # Environment configuration template
```

## Setup Instructions

**1. Environment Configuration**
Create a `.env` file in the root directory using `.env.example` as a template:
```ini
GMAIL_PASS_KEY="your-google-app-password"
```
*Note: A Google App Password securely generated from your Google Account settings is required to authenticate the IMAP connection.*

**2. Virtual Environment Initialization**
```bash
# Windows
.\venv\Scripts\activate
```

**3. Dependency Installation**
```bash
pip install -r requirements.txt
```

## Usage

Navigate to the `backend` directory and execute the main application entry point to initiate the listener service:

```bash
cd backend
python main.py
```
*Note for Evaluators: Executing `main.py` automatically initializes the real-time monitoring routines defined in `listener.py`.*

To gracefully terminate the listener process, input `Ctrl+C` in the terminal.

## Validation and Testing

The detection environment currently supports two evaluation workflows:
- **Keyword Override (Active):** A manual test flag that automatically routes any email containing the exact word "phishing" in the subject line to the quarantine folder.
- **ML Integration (Pending):** The `get_phishing_score()` function is provisioned as an architectural placeholder to accept integration with trained classification models. It currently defaults to a benign baseline execution score for integration testing purposes.