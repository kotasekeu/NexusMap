# Evoluční optimalizace Kohonenovy samo-organizační mapy (SOM)

Tento nástroj slouží k automatické optimalizaci parametrů Kohonenovy neuronové sítě pomocí evolučního algoritmu. Cílem je najít takové nastavení, které minimalizuje kvantizační chybu při zpracování vstupních dat.

---

## 📁 Struktura projektu

- `evolutionary_som.py` – hlavní skript pro spuštění evoluce
- `evolutionary_som_config.py` – konfigurace parametrového prostoru
- `kohonen_24_04_17.py` – implementace Kohonenovy sítě
- `/userfiles/evolution/` – adresář pro výsledky, zálohy, cache a logy

---

## ⚙️ Spuštění

1. Uprav `evolutionary_som_config.py` podle potřeby:
   - počet generací (`generations`)
   - velikost populace (`population_size`)
   - varianty parametrů (`param_space`)
   - vstupní rozměry (`sample_size`, `input_dim`)
   - další nastavení

2. Spusť skript:

```bash
python evolutionary_som.py
```

---

## 📊 Výstupy

Výstupy běhu jsou ukládány do `/userfiles/evolution/`:

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

Volitelně lze sledovat i poměr `chyba / čas`.

---

## ⚡ Vlastnosti

- ✅ Paralelní zpracování (využití více jader)
- ✅ Automatické zálohování výsledků
- ✅ Jednoduchá správa dat (cache podle vstupních parametrů)
- ✅ Rozšiřitelnost o další metriky a metody optimalizace

---

## 🔁 Jak funguje evoluce

- Vytvoření počáteční náhodné populace
- Vyhodnocení všech konfigurací
- Výběr nejlepší poloviny + mutace
- Opakování po zadaný počet generací

---

## 📌 Poznámky

- Pokud chceš testovat pouze jeden parametr, nech ostatní fixní
- UID konfigurací slouží pro dohledání konkrétního výsledku napříč soubory

---

## 🧼 Reset mezi běhy

- Při každém spuštění se staré výsledky přesunou do `backup-*`
- Zachovává se pouze `input.csv`, pokud existuje
