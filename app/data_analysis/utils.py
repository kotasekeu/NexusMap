import os
import shutil

# Globální proměnná pro uid_hash
_uid_hash = None

def set_uid_hash(uid_hash: str) -> None:
    """Nastaví globální uid_hash pro logování."""
    global _uid_hash
    _uid_hash = uid_hash

def log_message(message: str) -> None:
    """Zapíše zprávu do souboru log.txt včetně data a času."""
    if _uid_hash:
        log_file = f"/userfiles/{_uid_hash}/log.txt"
    else:
        log_file = "/app/data_analysis/log.txt"
    from datetime import datetime
    current_time = datetime.now()
    with open(log_file, "a") as log:
        log.write(f"{current_time} {message}\n")

def read_csv(file_path: str) -> list:
    """Načte CSV soubor a vrátí data jako seznam."""
    pass

def save_csv(data: list, file_path: str) -> None:
    """Uloží seznam dat do CSV souboru."""
    pass

def clear_files(uid_hash: str) -> None:
    """Smaže všechny soubory v adresáři pro daný uid_hash, kromě souboru input.csv."""
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
                    print(f"Chyba při mazání souboru {filename}: {e}")