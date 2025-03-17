def log_message(message: str) -> None:
    """Zapíše zprávu do souboru log.txt."""
    log_file = "/app/log.txt"
    with open(log_file, "a") as log:
        log.write(f"{message}\n")

def read_csv(file_path: str) -> list:
    """Načte CSV soubor a vrátí data jako seznam."""
    pass

def save_csv(data: list, file_path: str) -> None:
    """Uloží seznam dat do CSV souboru."""
    pass