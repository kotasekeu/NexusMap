# FrontEnd Module

## Ukázková struktura složky:

├── Customers/                      <br>
│   ├── Forms/                      <br>
│   │   └── CustomerFormFactory.php <br>
│   ├── Presenter/                  <br>
│   │   └── CustomersPresenter.php  <br>
│   ├── Service/                    <br>
│   │   └── CustomerService.php     <br>
│   ├── Templates/                  <br>
│   │    └── detail.latte

- `Forms/`
    - `CustomerFormFactory.php`: Factory třída pro vytváření formulářů, zahrnuje validace a nastavení.

- `Presenter/`
    - `CustomersPresenter.php`: Presenter řídí interakci mezi uživatelským rozhraním a modelem, zpracovává uživatelské požadavky a aktualizuje zobrazení.

- `Service/`
    - `CustomerService.php`: Service vrstva obsluhuje specifické služby, jako jsou API volání, zpracování odpovědí a cachování dat.

- `templates/`
    - `detail.latte`: Latte šablona pro zobrazení dat.
