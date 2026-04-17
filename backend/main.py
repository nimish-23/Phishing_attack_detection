import os
import sys

# Add 'service' to the Python path so the internal imports in `service/` work properly
sys.path.append(os.path.join(os.path.dirname(__file__), 'service'))

from service.listener import start_idle_listener

def main():
    print("[SYSTEM] Starting Phishing Detection Backend...")
    try:
        # Start the continuous email listener
        start_idle_listener()
    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutting down gracefully...")
    except Exception as e:
        print(f"[SYSTEM] Encountered an error: {e}")

if __name__ == "__main__":
    main()
