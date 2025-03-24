# API Module

## Ukázková struktura složky:

├── Customers/                      <br>
│   ├── Entity/                     <br>
│   │   └── Customer.php            <br>
│   ├── Facade/                     <br>
│   │   ├── CustomerFacade.php      <br>
│   │   └── CustomerCronTrait.php   <br>
│   ├── Forms/                      <br>
│   │   └── CustomerFormFactory.php <br>
│   ├── Model/                      <br>
│   │   └── CustomerModel.php       <br>
│   ├── Presenter/                  <br>
│   │   └── CustomersPresenter.php  <br>
│   ├── Service/                    <br>
│   │   └── CustomerService.php     <br>
│   └── templates/                  <br>
│       └── detail.latte

- `Entity/`
  - `Customer.php`: Definuje datovou strukturu pro entity, používáno primárně pro mapování dat z API a databáze.

- `Facade/`
  - `CustomerFacade.php`: Fasáda poskytuje složitější logiku pro práci s daty, zpracovává vícevrstvé operace.
  - `CustomerCronTrait.php`: Trait pro cron úlohy spojené, umožňuje snadné začlenění opakovaných úloh do fasád.

- `Forms/`
  - `CustomerFormFactory.php`: Factory třída pro vytváření formulářů, zahrnuje validace a nastavení.

- `Model/`
  - `CustomerModel.php`: Model obsahuje business logiku a operace pro zpracování dat, jako je načítání, uložení a manipulace s daty.

- `Presenter/`
  - `CustomersPresenter.php`: Presenter řídí interakci mezi uživatelským rozhraním a modelem, zpracovává uživatelské požadavky a aktualizuje zobrazení.

- `Service/`
  - `CustomerService.php`: Service vrstva obsluhuje specifické služby, jako jsou API volání, zpracování odpovědí a cachování dat.

- `templates/`
  - `detail.latte`: Latte šablona pro zobrazení dat.
