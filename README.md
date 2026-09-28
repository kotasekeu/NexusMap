# NexusMap - Analýza a vizualizace dat pomocí Kohonenovy mapy

Tento modul implementuje zpracování dat, trénování Kohonenovy samo-organizační mapy (SOM) a vizualizaci výsledků. Modul je součástí většího systému pro analýzu a vizualizaci dat.

## 📁 Struktura projektu

- `main.py` - Hlavní vstupní bod aplikace, zpracování argumentů příkazové řádky
- `project_processor.py` - Zpracování projektů a dat, hlavní logika analýzy
- `visualization.py` - Vizualizace výsledků SOM (U-matrix, komponentní plány, koláčové grafy)
- `kohonen.py` - Implementace Kohonenovy SOM sítě a trénovací algoritmy
- `preprocess.py` - Předzpracování vstupních dat (normalizace, kódování)
- `utils.py` - Pomocné funkce pro logování a práci se soubory
- `database.py` - Práce s databází, správa projektů a jejich stavů
- `requirements.txt` - Seznam závislostí pro Python
- `Dockerfile` - Konfigurace Docker kontejneru
- `docker-compose.yml` - Konfigurace Docker služeb

## 🐳 Instalace a nasazení

Projekt je kontejnerizován pomocí Dockeru. Pro nasazení:

1. Ujistěte se, že máte nainstalovaný Docker a Docker Compose
2. Sestavte a spusťte kontejnery:
```bash
docker-compose up -d
```

## 🚀 Použití

### Automatické spouštění

Projekt je nastaven pro automatické spouštění pomocí cronu, který kontroluje projekty ve stavu:
- `status = 0` (nový projekt)
- `ready_to_analyze = 1` (připraven k analýze)

Cron job by měl být nastaven na pravidelnou kontrolu nových projektů, například každých 5 minut:
```bash
*/5 * * * * cd /cesta/k/projektu && python3 project_processor.py
```

### Manuální spuštění

Pro manuální spuštění analýzy konkrétního projektu:

```bash
python3 project_processor.py <uid_hash>
```

Například:
```bash
python3 project_processor.py nxmpp68236ed7373696.56328909
```

## 📊 Výstupy

Výstupy jsou ukládány do složky projektu ve struktuře:

| Složka/Soubor | Popis |
|---------------|-------|
| `csv/` | Původní a zpracovaná CSV data |
| `json/` | Výsledky analýzy ve formátu JSON |
| `visualization/` | Generované vizualizace |
| `pie_data_*.json` | Data pro koláčové grafy jednotlivých kategorií |
| `weights.npy` | Naučené váhy SOM sítě |
| `kohonen-log.txt` | Log trénování SOM |

### Struktura složek

```
project_folder/
├── csv/              # Vstupní a zpracovaná data
├── json/             # Výsledky analýzy
├── visualization/    # Generované vizualizace
├── pie_data_*.json   # Data pro koláčové grafy
├── weights.npy       # Naučené váhy
└── kohonen-log.txt   # Log trénování
```

## 📝 Logování

Modul `utils.py` zajišťuje logování do souboru `kohonen-log.txt`. Log obsahuje:
- Časové razítko
- Zprávu
- ID projektu (uid_hash)

Logy jsou ukládány do složky projektu a obsahují informace o:
- Průběhu trénování
- Chybách a varováních
- Stavu zpracování dat
- Výsledcích analýzy

Příklad logu:
```
2024-03-20 10:15:30.123456 Začátek trénování SOM nxmpp68236ed7373696.56328909
2024-03-20 10:15:35.234567 Epocha 1/100, MQE: 0.723 nxmpp68236ed7373696.56328909
```

## 🔧 Konfigurace

Konfigurace se načítá z databáze z atributů `project_settings` a `som_settings`. Pokud nejsou nastaveny SOM parametry, použijí se výchozí hodnoty z `kohonen.py`.

### Nastavení projektu (`project_settings`)

```json
{
    "selected_columns": ["Id", "SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm", "Species"],
    "primary_id": "Id",
    "analysis_columns": ["Id", "SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm", "Species"],
    "legend_column": "Species",
    "legend_title": "Druhy",
    "categorical_column": ["Species"],
    "numerical_column": ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"],
    "string_column": [],
    "categorical_groups": {}
}
```

#### Popis parametrů projektu

| Parametr | Popis | Nastavení |
|----------|-------|-----------|
| `selected_columns` | Sloupce vybrané uživatelem | Uživatel |
| `primary_id` | Identifikátor záznamu | Uživatel |
| `analysis_columns` | Sloupce pro analýzu | Uživatel |
| `legend_column` | Sloupec pro legendu | Uživatel |
| `legend_title` | Název legendy | Uživatel |
| `categorical_column` | Kategorické sloupce | Automaticky |
| `numerical_column` | Numerické sloupce | Automaticky |
| `string_column` | Textové sloupce | Automaticky |
| `categorical_groups` | Skupiny kategoriálních sloupců podle prefixu | Automaticky |

### Nastavení SOM (`som_settings`)

Parametry pro Kohonenovu SOM síť. Pokud nejsou nastaveny, použijí se výchozí hodnoty z `kohonen.py`.

```json
{
    "learning_rate": 0.9,
    "min_learning_rate": 0.025,
    "radius": 10.0,
    "min_radius": 1.0,
    "num_batches": 10,
    "max_batch_percent": 5.0,
    "min_batch_percent": 0.2,
    "lr_decay_type": "linear-drop",
    "radius_decay_type": "linear-drop",
    "batch_growth_type": "exp-growth",
    "random_seed": 42,
    "growth_g": 15.0,
    "m": 20,
    "n": 20,
    "epoch_multiplier": 1.0,
    "min_q_error": null,
    "map_type": "square",
    "normalize_weights_flag": false,
    "max_epochs_without_improvement": null
}
```

#### Popis parametrů SOM

| Parametr | Popis | Výchozí hodnota |
|----------|-------|-----------------|
| `learning_rate` | Počáteční rychlost učení | 0.9 |
| `min_learning_rate` | Minimální rychlost učení | 0.025 |
| `radius` | Počáteční poloměr sousedství | 10.0 |
| `min_radius` | Minimální poloměr sousedství | 1.0 |
| `num_batches` | Počet dávkových iterací | 10 |
| `max_batch_percent` | Maximální velikost dávky (% dat) | 5.0 |
| `min_batch_percent` | Minimální velikost dávky (% dat) | 0.2 |
| `lr_decay_type` | Typ poklesu rychlosti učení | "linear-drop" |
| `radius_decay_type` | Typ poklesu poloměru | "linear-drop" |
| `batch_growth_type` | Typ růstu velikosti dávky | "exp-growth" |
| `random_seed` | Semeno pro náhodný generátor | 42 |
| `growth_g` | Parametr růstu dávky | 15.0 |
| `m`, `n` | Rozměry mapy | 20, 20 |
| `epoch_multiplier` | Násobitel počtu epoch | 1.0 |
| `min_q_error` | Minimální kvantizační chyba pro early stopping | null |
| `map_type` | Typ mřížky ("square" nebo "hex") | "square" |
| `normalize_weights_flag` | Normalizace vah | false |
| `max_epochs_without_improvement` | Maximální počet epoch bez zlepšení | null |

#### Typy poklesu a růstu

- `lr_decay_type` a `radius_decay_type`:
  - `"linear-drop"`: Lineární pokles
  - `"exp-drop"`: Exponenciální pokles
  - `"inv-drop"`: Inverzní pokles

- `batch_growth_type`:
  - `"exp-growth"`: Exponenciální růst
  - `"linear-growth"`: Lineární růst

## 📈 Vizualizace

Modul `visualization.py` poskytuje následující typy vizualizací:

- U-matrix (topografická mapa)
- Komponentní plány
- Koláčové grafy pro kategorické proměnné
- Heatmapy pro numerické proměnné

## 🗄️ Databáze

Modul `database.py` zajišťuje:

- Ukládání a načítání projektů
- Aktualizaci stavu analýzy
- Správu nastavení projektů

## 🔄 Předzpracování dat

Modul `preprocess.py` provádí:

- Normalizaci numerických proměnných
- Kódování kategoriálních proměnných
- Detekci a zpracování chybějících hodnot
- Filtrování prázdných řádků

## ⚡ Vlastnosti

- ✅ Paralelní zpracování
- ✅ Automatické zálohování výsledků
- ✅ Podpora vlastních vstupních dat
- ✅ Flexibilní konfigurace
- ✅ Interaktivní vizualizace
- ✅ Detekce extrémů a odlehlých hodnot
- ✅ Podpora hexagonální a čtvercové mřížky
- ✅ Early stopping pro optimalizaci trénování

## 🚧 TODO / Chybějící funkce

- [ ] Implementace dalších typů mřížky
- [ ] Podpora pro více typů fitness funkcí
- [ ] Vizualizace průběhu trénování
- [ ] Možnost pokračování v trénování z předchozího stavu
- [ ] Vylepšení dokumentace API
- [ ] Přidání unit testů
- [ ] Optimalizace výkonu pro velké datové sady

## 📝 Poznámky

- Pro replikovatelnost výsledků lze nastavit `random_seed`
- Hexagonální mřížka může poskytnout lepší výsledky pro některé typy dat
- Early stopping může výrazně zrychlit trénování při zachování kvality
- Pro velké datové sady doporučujeme použít paralelní zpracování