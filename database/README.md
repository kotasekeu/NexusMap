# Databázová struktura projektu NexusMap

Tento adresář obsahuje všechny potřebné soubory pro správu databáze projektu NexusMap.

## Struktura adresářů

- `schema/` - Obsahuje SQL soubory pro vytvoření struktury databáze
  - `00_init.sql` - Základní nastavení databáze
  - `01_tables.sql` - Definice tabulek a jejich vztahů
- `data/` - Obsahuje SQL soubory s daty
  - `01_base_data.sql` - Základní data potřebná pro běh aplikace
  - `02_test_data.sql` - Testovací data pro vývoj
- `migrations/` - Obsahuje migrační soubory pro aktualizaci databáze

## Instalace databáze

1. Vytvořte novou databázi:
```sql
CREATE DATABASE nexusmap CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Importujte soubory v následujícím pořadí:
```bash
mysql -u username -p nexusmap < schema/00_init.sql
mysql -u username -p nexusmap < schema/01_tables.sql
mysql -u username -p nexusmap < data/01_base_data.sql
```

3. Pro vývojové prostředí můžete importovat i testovací data:
```bash
mysql -u username -p nexusmap < data/02_test_data.sql
```

## Struktura databáze

Databáze obsahuje následující hlavní tabulky:

- `customers` - Uživatelé systému
- `customer_type` - Typy uživatelů
- `projects` - Projekty pro analýzu
- `source_files` - Zdrojové soubory pro analýzu
- `front_routes` - Definice rout pro frontend

## Migrace

Pro aktualizaci databáze použijte migrační soubory v adresáři `migrations/`. Migrace se aplikují automaticky při spuštění aplikace.

## Zálohování

Pro zálohování databáze použijte:
```bash
mysqldump -u username -p nexusmap > backup.sql
``` 