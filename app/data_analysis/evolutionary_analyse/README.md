# Evoluční optimalizace Kohonenovy samo-organizační mapy (SOM)

Tento nástroj slouží k automatické optimalizaci parametrů Kohonenovy neuronové sítě pomocí evolučního algoritmu. Cílem je najít takové nastavení, které minimalizuje kvantizační chybu při zpracování vstupních dat.

---

## 📁 Struktura projektu

- `evolutionary_som.py` – hlavní skript pro spuštění evoluce
- `evolutionary_som_config.py` – výchozí konfigurace parametrového prostoru
- `./reports/` – adresář pro výsledky, zálohy, cache a logy. Adresář je vytvořen:
  - V adresáři vstupního souboru (pokud je zadán)
  - V aktuálním adresáři (pokud není zadán vstupní soubor)

---

## ⚙️ Spuštění

1. Vytvoř vlastní konfigurační soubor (volitelné):
   ```json
   {
       "population_size": 20,
       "generations": 10,
       "uid_prefix": "my_experiment",
       "learning_rate": [0.9, 0.8, 0.7],
       "min_learning_rate": [0.3, 0.2, 0.1],
       "radius": [10.0, 5.0, 2.0],
       "min_radius": [1.0, 0.5, 0.2],
       "num_batches": 10,
       "min_batch_percent": [1.0, 0.5, 0.2],
       "max_batch_percent": [10.0, 5.0, 2.0],
       "lr_decay_type": ["linear-drop", "exp-drop"],
       "radius_decay_type": ["linear-drop", "exp-drop"],
       "batch_growth_type": ["exp-growth", "linear-growth"],
       "random_seed": null,
       "growth_g": [5.0, 10.0, 15.0],
       "sample_size": 500,
       "input_dim": 4,
       "map_size": [20, 20],
       "epoch_multiplier": [1.0, 5.0, 10.0],
       "min_q_error": null,
       "map_type": "square",
       "normalize_weights_flag": [false, true],
       "max_epochs_without_improvement": null
   }
   ```

2. Spusť skript s volitelnými parametry:

```bash
# Základní spuštění s výchozí konfigurací
python evolutionary_som.py
# Výstupy budou v ./reports/

# Spuštění s vlastním konfiguračním souborem
python evolutionary_som.py --config config.json
# Výstupy budou v ./reports/

# Spuštění s vlastním vstupním souborem a konfigurací
python evolutionary_som.py --input data.csv --config config.json
# Výstupy budou v ./data/reports/
```

---

## 📊 Výstupy

Výstupy běhu jsou ukládány do složky `reports` v příslušném adresáři:

| Soubor                    | Popis                                                         |
|---------------------------|---------------------------------------------------------------|
| `log.txt`                 | Log vyhodnocení konfigurací (UID, skóre, doba)               |
| `results.csv`             | CSV výstup s parametry, chybou a dobou zpracování            |
| `progress.log`            | Přehled průběhu – kolik z celkového počtu hotovo             |
| `final_best.txt`          | Nejlepší konfigurace z každé generace                        |
| `data_{sample}x{dim}.npy` | Vygenerovaná vstupní data pro daný rozměr a počet vzorků     |
| `backup-YYYY-MM-DD...`    | Automatická záloha předchozího běhu                          |

---

## 🧠 Hodnocení konfigurací

- **Kvantizační chyba** – čím menší, tím lepší
- **Doba výpočtu** – sekundová doba výpočtu jedné konfigurace
- **Fitness funkce** – kombinace chyby a času s váhami:
  - W_ERROR = 0.7 (váha pro kvantizační chybu)
  - W_TIME = 0.3 (váha pro dobu výpočtu)

---

## ⚡ Vlastnosti

- ✅ Paralelní zpracování (využití více jader)
- ✅ Automatické zálohování výsledků
- ✅ Jednoduchá správa dat (cache podle vstupních parametrů)
- ✅ Podpora vlastních vstupních dat
- ✅ Rozšiřitelnost o další metriky a metody optimalizace

---

## 🔁 Jak funguje evoluce

1. **Inicializace**:
   - Vytvoření počáteční náhodné populace
   - Načtení vstupních dat (soubor nebo generovaná data)

2. **Hodnocení generace**:
   - Paralelní vyhodnocení všech konfigurací
   - Výpočet fitness pro každého jedince
   - Normalizace chyb a časů pro srovnatelnost

3. **Selekce a reprodukce**:
   - Výběr nejlepší poloviny populace
   - Uniformní křížení vybraných jedinců
   - Mutace nových konfigurací
   - Opakování po zadaný počet generací

---

## 📌 Poznámky

- Pokud chceš testovat pouze jeden parametr, nech ostatní fixní
- UID konfigurací slouží pro dohledání konkrétního výsledku napříč soubory
- Vstupní data lze zadat buď jako CSV soubor, nebo se automaticky vygenerují
- Pro replikovatelnost výsledků lze nastavit `random_seed`

---

## 🔄 Reset mezi běhy

- Při každém spuštění se staré výsledky přesunou do `backup-*`
- Zachovává se pouze `input.csv`, pokud existuje
- Cache vygenerovaných dat se zachovává pro opakované použití
