from api_request import get_package, send_api_request
from ui import clear_screen, pause
import time

def enter_sentry_mode():
    clear_screen()
    print("Entering Sentry Mode...")
    print("Press Ctrl+C to exit.")
    
    in_sentry = True
    while in_sentry:
        fetch_timestamp = int(time.time())
        print(f"Fetching data at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fetch_timestamp))}")