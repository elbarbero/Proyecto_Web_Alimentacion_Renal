import os
import sys
import subprocess
import time
from pyngrok import ngrok, conf

def main():
    # 1. Load configuration (Token)
    token = None
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('NGROK_AUTHTOKEN='):
                    token = line.strip().split('=', 1)[1]
                    break
    
    if not token:
        print(" Error: NGROK_AUTHTOKEN not found in .env")
        return

    print(" Configuring Ngrok...")
    # Set the token
    ngrok.set_auth_token(token)

    # 2. Start the Local Server (server.py)
    print("Starting local server...")
    server_process = subprocess.Popen([sys.executable, "server.py"])
    
    # Wait a bit for server to spin up
    time.sleep(2)

    try:
        # 3. Open the Tunnel
        print("Opening secure tunnel...")
        # config = conf.PyngrokConfig(monitor_thread=False)
        public_url = ngrok.connect(8000).public_url
        
        print("\n" + "="*60)
        print(f" APP ONLINE! Access it via this Global URL:")
        print(f" > {public_url}")
        print("="*60 + "\n")
        print("Press Ctrl+C to stop.")

        # Keep alive
        server_process.wait()

    except KeyboardInterrupt:
        print("\nCheck finished.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Shutting down...")
        if server_process:
            server_process.terminate()
        ngrok.kill()

if __name__ == "__main__":
    main()
