import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from plyer import notification

class EmailHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.msg'):
            filename = os.path.basename(event.src_path)
            self.show_notification(f"New Advisor View Received!\n\n{filename}\n\nPlease open the Compliance Tracker app to review.")

            # Auto-launch the app
            try:
                # We use start to run the batch file asynchronously so it doesn't block the watcher
                subprocess.Popen(['cmd.exe', '/c', 'start', 'run_app.bat'])
            except Exception as e:
                print(f"Failed to auto-launch app: {e}")

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
    from config import EMAILS_DIR
    path = EMAILS_DIR
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
