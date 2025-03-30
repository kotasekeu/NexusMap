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


## Co dodělat a jak postupovat.

- možnost výběru generované mapy - hexa, body, další. 
- anonymizace dat
- front rozhraní co zkontroluje po nahrání souboru csv sloupce a nastaví co s nimi (doporučení + potvrzení uživatelem)
- vyřešit přesun dat mezi /var a example public - asi přístup přes API






## Nastavování před zpracováním

Sloupce, které se budou brát v úvahu pro generování SOM mapy. Ostatní data z CSV souboru se neberou v potaz, pouze se vypisují do reportu
- selected_columns = ['event_type', 'country', 'duration', 'cost']

Sloupce, které se budou převádět z kategoriálních na numerické (jsou to stringy ale pro potřeby analýzy je potřeba udělat z nich číselné hodnoty
- categorical_columns = ['event_type', 'country']

Sloupce pro analýzu clusterů
- analysis_columns = ['cost', 'duration']  # Sloupce, pro které se počítají průměry a hledají extrémyfile.csv

Sloupec, podle kterého se vygeneruje legenda a jaký bude název legendy
- legend_column = 'country'
- legend_title = 'Země'

Sloupce, které je nutné ošetřit NaN hodnotami a na jakou hodnotu
- 'nan_replacement = {
-    'cost': 0,
-    'duration': 0
-     'duration': 'mean',  # Pokud chceme nenastavenou hodnotu převádět na průměrnou hodnotu
-     'purpose': 'N/A'  # Pevná hodnota pro string


vizualizovat clustery na mapě, po najetí zobrazit popupbox a info, link na detail daného clusteru, zvýraznit clustery s extrémy
optimalizace rychlosti


Z root  - phpdoc run -d app/api/app -t docs/api