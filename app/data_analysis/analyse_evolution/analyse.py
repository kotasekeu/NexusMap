import pandas as pd

# Načtení dat
df = pd.read_csv("results.csv")

# Výpočet skóre
df["score_combined"] = df["score"] * df["duration"] * df["total_weight_updates"]

# Sloupce nepatřící do konfigurace
non_config_cols = [
    "uid", "score", "duration", "total_weight_updates",
    "score_combined", "config_key", "config_count"
]

# Dynamické určení konfiguračních sloupců
compare_cols = [col for col in df.columns if col not in non_config_cols and not col.startswith("Unnamed")]

# Klíč konfigurace
df["config_key"] = df[compare_cols].astype(str).agg("|".join, axis=1)

# Nejlepší řádky pro každou konfiguraci
best_rows = df.loc[df.groupby("config_key")["score_combined"].idxmin()].copy()
best_rows["config_count"] = df.groupby("config_key")["uid"].transform("count")

# Seřazení
best_sorted = best_rows.sort_values("score_combined")

# Uložení plné tabulky
best_sorted.to_csv("best_configurations_full.csv", index=False)

# Zjištění statických parametrů
static_cols = [col for col in compare_cols if df[col].nunique(dropna=False) == 1]

# Vítězná konfigurace
winner = best_sorted.iloc[0]

# Zápis do TXT souboru
with open("summary.txt", "w", encoding="utf-8") as f:
    f.write("Best configuration:\n")
    for col in compare_cols:
        f.write(f"{col}: {winner[col]}\n")
    f.write("\nStatic parameters:\n")
    for col in static_cols:
        f.write(f"{col} = {df[col].iloc[0]}\n")