import sys
import os
import json
import urllib.request
import urllib.error
from backend.config import GEMINI_API_KEY

print(f"API Key present: {'Yes' if GEMINI_API_KEY else 'No'}")
if not GEMINI_API_KEY:
    sys.exit(1)

def test_model(model_name):
    print(f"\nTesting model: {model_name}")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Hello, say 'OK'."}]}]
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print("SUCCESS")
            # print(json.dumps(result, indent=2))
            return True
    except urllib.error.HTTPError as e:
        print(f"FAILED: HTTP {e.code}")
        print(e.read().decode())
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

models_to_test = [
    "gemini-flash-lite-latest",  # What was in the code
    "gemini-1.5-flash",          # The standard
    "gemini-2.0-flash-exp",      # Experimental
    "gemini-pro"                 # Old standard
]

for m in models_to_test:
    if test_model(m):
        print(f"\nFind valid model: {m}")
        break
