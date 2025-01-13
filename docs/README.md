# Nette + Python Data Processing Project

## Popis projektu
Projekt kombinuje Nette framework pro frontend s Python skripty pro analýzu dat. Zpracování dat probíhá na pozadí pomocí cron jobu, který spouští Python skripty každou minutu.

## Struktura projektu
- **app/** – Nette aplikace
- **scripts/** – Python skripty pro zpracování CSV
- **docker/** – Docker soubory
- **data/** – Data ke zpracování (input/output)
- **tests/** – Testy aplikace



/app/core - zdrojáky

/app/main.py - základní soubor, který se spouští s najetím prostředí, inicializace API, route, cronu atd

/app/core/cron.py - skript, který se spouší (bude) každou minutu a hledá nejstarší neanalyzovaný projekt a spustí ho, spadá spíše do examples. Následně odstranit.

cron.py spouští analysis.py - načte detail project z DB s nastavením projektu

ten spustí metodu z preprocess, která provede úpravu vstupního souboru input.csv na processed.csv


