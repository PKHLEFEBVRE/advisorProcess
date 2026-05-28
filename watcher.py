import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from plyer import notification

class EmailHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.msg'):
            filename = os.path.basename(event.src_path)
            self.show_notification(f"New Advisor View Received!\n\n{filename}\n\nPlease open the Compliance Tracker app to review.")

    def show_notification(self, message):
        try:
            notification.notify(
                title='Compliance Tracker',
                message=message,
                app_name='Compliance Tracker',
                timeout=10
            )
        except Exception as e:
            print(f"Notification failed: {e}")

if __name__ == "__main__":
    path = os.path.abspath("emails")
    if not os.path.exists(path):
        os.makedirs(path)

    event_handler = EmailHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    print(f"Monitoring '{path}' for new .msg files...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
