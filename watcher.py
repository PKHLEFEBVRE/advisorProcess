import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter as tk
from tkinter import messagebox
import threading

class EmailHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.eml'):
            filename = os.path.basename(event.src_path)
            self.show_notification(f"New Advisor View Received!\n\n{filename}\n\nPlease open the Compliance Tracker app to review.")

    def show_notification(self, message):
        def _notify():
            # Create a simple Tkinter window for notification (since plyer/win10toast can be finicky in pure headless/cross-platform envs)
            root = tk.Tk()
            root.withdraw() # Hide main window
            root.attributes('-topmost', True) # Keep on top
            messagebox.showinfo("Compliance Tracker", message, parent=root)
            root.destroy()

        # Run notification in a separate thread so it doesn't block the watcher
        threading.Thread(target=_notify).start()

if __name__ == "__main__":
    path = os.path.abspath("emails")
    if not os.path.exists(path):
        os.makedirs(path)

    event_handler = EmailHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    print(f"Monitoring '{path}' for new .eml files...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
