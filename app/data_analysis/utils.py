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
        log_file = f"/userfiles/{_uid_hash}/kohonen-log.txt"
    else:
        log_file = "./kohonen-log.txt"
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
    """Moves all files and the visualization directory in the directory for the given uid_hash to a new directory named backup-{timestamp}, except for the input.csv file."""
    from datetime import datetime
    directory = f"/userfiles/{uid_hash}"
    backup_dir = f"/userfiles/{uid_hash}/backup-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if filename != "input.csv":
                if os.path.isdir(file_path) and filename == "visualization":
                    try:
                        shutil.move(file_path, backup_dir)
                    except Exception as e:
                        print(f"Error moving directory {filename}: {e}")
                elif os.path.isfile(file_path):
                    try:
                        shutil.move(file_path, backup_dir)
                    except Exception as e:
                        print(f"Error moving file {filename}: {e}")