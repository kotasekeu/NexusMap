"""
Pomocný modul pro logování a práci se soubory.

Tento modul poskytuje funkce pro:
- Nastavení a správu ID projektu (uid_hash)
- Logování zpráv do souboru s časovým razítkem
"""

from datetime import datetime

# Globální proměnná pro ukládání ID projektu
_uid_hash = None

def set_uid_hash(uid_hash: str) -> None:
    """Nastaví globální ID projektu pro logování.
    
    Args:
        uid_hash (str): Unikátní identifikátor projektu
        
    Note:
        Tato funkce musí být volána před jakýmkoliv logováním,
        aby se zprávy ukládaly do správné složky projektu.
    """
    global _uid_hash
    _uid_hash = uid_hash

def log_message(message: str) -> None:
    """Zapíše zprávu do logovacího souboru včetně časového razítka.
    
    Args:
        message (str): Zpráva k zalogování
        
    Note:
        Pokud není nastaveno uid_hash, loguje se do aktuálního adresáře.
        Jinak se loguje do složky projektu v /userfiles/{uid_hash}/.
    """
    if _uid_hash:
        log_file = f"/userfiles/{_uid_hash}/kohonen-log.txt"
    else:
        log_file = "./kohonen-log.txt"
        
    current_time = datetime.now()
    with open(log_file, "a") as log:
        log.write(f"{current_time} {message} {_uid_hash}\n")