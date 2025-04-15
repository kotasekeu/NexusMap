import os
import shutil

# Global variable for uid_hash
_uid_hash = None

def set_uid_hash(uid_hash: str) -> None:
    """Set the global uid_hash for logging."""
    global _uid_hash
    _uid_hash = uid_hash

def log_message(message: str) -> None:
    """Write a message to the log.txt file including date and time."""
    if _uid_hash:
        log_file = f"/userfiles/{_uid_hash}/log.txt"
    else:
        log_file = "/app/data_analysis/log.txt"
    from datetime import datetime
    current_time = datetime.now()
    with open(log_file, "a") as log:
        log.write(f"{current_time} {message}\n")

# # not needed yet
# def read_csv(file_path: str) -> list:
#     """Reads a CSV file and returns the data as a list."""
#     pass
#
# def save_csv(data: list, file_path: str) -> None:
#     """Saves a list of data to a CSV file."""
#     pass

def clear_files(uid_hash: str) -> None:
    """Deletes all files in the directory for the given uid_hash, except for the input.csv file."""
    directory = f"/userfiles/{uid_hash}"
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename != "input.csv":
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error deleting file {filename}: {e}")