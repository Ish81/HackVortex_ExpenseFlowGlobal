
# src/watcher.py
import time
import os

class FileWatcher:
    def _init_(self, directory_to_watch, callback):
        self.directory = directory_to_watch
        self.callback = callback
        self.seen_files = set(os.listdir(directory_to_watch)) # Initialize with existing files
        print(f"FileWatcher initialized for directory: {self.directory}")

    def start_watching(self, interval=5):
        print(f"Starting file watcher. Checking every {interval} seconds...")
        while True:
            current_files = set(os.listdir(self.directory))
            new_files = current_files - self.seen_files
            if new_files:
                for file_name in new_files:
                    file_path = os.path.join(self.directory, file_name)
                    print(f"  New file detected: {file_path}")
                    self.callback(file_path) # Call the provided callback function
                self.seen_files = current_files # Update seen files
            time.sleep(interval)

# Example usage (not directly used in run_pipeline.py yet)
# from src.orchestrator import Orchestrator
# def process_new_file(file_path):
#     orchestrator = Orchestrator()
#     processed_data = orchestrator.process_single_receipt(file_path, 999) # Placeholder ID
#     print(f"Finished processing new file: {file_path}, Data: {processed_data}")

# if _name_ == "_main_":
#     watcher = FileWatcher("data/incoming_receipts", process_new_file)
#     watcher.start_watching()