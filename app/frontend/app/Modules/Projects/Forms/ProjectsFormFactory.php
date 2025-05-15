<?php

declare(strict_types=1);

namespace App\Modules\Projects\Forms;

use App\Modules\Projects\Service\ProjectsService;
use App\Common\Factory\FormFactory;
use Nette;
use Nette\Application\UI\Form;
use Nette\Utils\ArrayHash;

/**
 * ProjectFormFactory class
 *
 * This class is responsible for creating and managing the project form.
 */
final class ProjectFormFactory
{
	use Nette\SmartObject;

	/** @var FormFactory */
	private $factory;

	private $projectsService;
	/**
	 * Constructor for ProjectFormFactory class
	 *
	 * @param FormFactory	$factory	Form factory.
	 */
	public function __construct(
		FormFactory					$factory,
		ProjectsService				$projectsService
	)
	{
		$this->factory				= $factory;
		$this->projectsService		= $projectsService;
	}

	/**
	 * Creates and configures the project form.
	 *
	 * @return Form The configured project form.
	 */
	public function createForm(callable $onSuccess): Form
	{
		$form = $this->factory->create();
		$form->addHidden('project_id');

		$form->addProtection('Platnost formuláře vypršela, obnovte stránku.');

		$form->addText('name', 'Název projektu')
			->setHtmlAttribute('class', 'form-control')
			->setRequired('Vyplňte název projektu');

		$form->addUpload('input_csv', 'Soubor pro analýzu')
			->setRequired('Nahrání souboru je povinné')
			->setHtmlAttribute('class', 'form-control')
			->addRule(Form::MaxFileSize, 'Maximální velikost je 32MB', 32 * 1024 * 1024)
			->addRule(Form::MimeType, 'Povoleny jsou pouze CSV soubory', "text/csv");

		$form->addSubmit('submit', 'Uložit projekt');

		$form->onValidate[] = function (Form $form, ArrayHash $values): void {
			if (empty($values->input_csv)) {
				$form->addError('Soubor nebyl nahraný.');
				return;
			}

			$csvContent = $values->input_csv->getContents();
			$lines = explode("\n", $csvContent);
			if (empty($lines)) {
				$form->addError('Soubor je prázdný.');
				return;
			}

			$firstLine = $lines[0];
			$columns = explode(',', $firstLine);
			if (empty($columns)) {
				$form->addError('První řádek souboru neobsahuje názvy sloupců oddělené čárkou.');
				return;
			}

			foreach ($columns as $column) {
				if (trim($column) === '') {
					$form->addError('Názvy sloupců nesmí být prázdné.');
					return;
				}
			}
		};

		$form->onSuccess[] = function (Form $form, ArrayHash $values) use ($onSuccess): void {

			$project_id = $this->projectsService->createProject($values);
			$onSuccess($project_id);
		};

		return $form;
	}

	public function editForm(callable $onSuccess, int $projectId): Form
	{
		$form = $this->factory->create();

		$form->addProtection('Platnost formuláře vypršela, obnovte stránku.');

		$form->addHidden('project_id');

		$form->addText('name', 'Název projektu')
			->setDisabled(true);

		$columnsNames	= $this->projectsService->getProjectConfigDescription();
		$columns		= $this->projectsService->getInputFileColumns($projectId);

		$form->addMultiSelect('selected_columns', $columnsNames['selected_columns'], $columns)
			->setRequired('Vyberte sloupce.')
			->setHtmlAttribute('class', 'form-select')
			->setOption('description', 'Vyberte sloupce z CSV, které chcete načíst a mít k dispozici v projektu. Neoznačené sloupce budou ignorovány. Můžete vybrat numerické, textové i kategorické sloupce.');

		$form->addSelect('primary_id', $columnsNames['primary_id'], $columns)
			->setPrompt('Vyberte')
			->setHtmlAttribute('class', 'form-select')
			->setRequired('Vyberte hlavní identifikátor')
			->setOption('description', 'Hlavní identifikátor je unikátní ID každého záznamu. Používá se pro identifikaci jednotlivých záznamů v průběhu analýzy, přiřazování k výsledkům (např. clusterům) a pro reportování odlehlých hodnot. Tento sloupec není přímo použit v numerických analytických výpočtech.');

		$form->addMultiSelect('analysis_columns', $columnsNames['analysis_columns'], $columns)
			->setRequired('Vyberte analytické sloupce')
			->setHtmlAttribute('class', 'form-select')
			->setOption('description', 'Z výše načtených `selected_columns` zde vyberte ty, které se použijí pro numerické analýzy (např. shlukování, detekce extrémů). Systém z nich automaticky vybere pouze numerické datové typy.');

		$form->addSelect('segmentation_column', $columnsNames['segmentation_column'], $columns)
			->setPrompt('Vyberte')
			->setHtmlAttribute('class', 'form-select')
			->setRequired('Vyberte sloupec legendy')
			->setOption('description', 'Vyberte sloupec (typicky kategorický), jehož hodnoty se použijí pro seskupování či segmentaci dat pro specifické analýzy nebo vizualizace (např. odlišení kategorií v grafech, filtrování). Nepoužívá se pro přímé generování legendy grafu.');

		$form->addText('std_threshold', 'Prahová hodnota pro extrémní hodnoty')
			->setRequired('Vyplňte prahovou hodnotu')
			->setHtmlAttribute('type', 'number')
			->setHtmlAttribute('min', '1')
			->setHtmlAttribute('max', '4')
			->setHtmlAttribute('step', '0.1')
			->addRule(Form::Float, 'Prahová hodnota musí být číslo')
			->addRule(Form::Range, 'Prahová hodnota musí být mezi 1 a 4', [1, 4])
			->setOption('description', 'Zadejte, kolik směrodatných odchylek od průměru musí hodnota překročit, aby byla považována za extrém. Např. hodnota 2 označí jen výrazné odchylky. Povolená hodnota je z intervalu 1 až 4.')
			->setDefaultValue(2);


		$form->addSubmit('submit', 'Uložit projekt');

		$form->onValidate[] = function (Form $form, ArrayHash $values): void {
			// form validation
		};

		$form->onSuccess[] = function (Form $form, ArrayHash $values) use ($onSuccess): void {

			$project_id = $this->projectsService->saveProjectSettings($values);
			$onSuccess($project_id);
		};

		return $form;
	}

	public function editSomForm(callable $onSuccess): Form
	{
		$form = $this->factory->create();

		$form->addProtection('Platnost formuláře vypršela, obnovte stránku.');

		$form->addHidden('project_id');

		$form->addText('name', 'Název projektu')
			->setDisabled(true);

		$form->addText('learning_rate', 'Počáteční rychlost učení')
			->setHtmlAttribute('type', 'number')
			->setRequired('Vyplňte rychlost učení')
			->setHtmlAttribute('min', '0.1')
			->setHtmlAttribute('max', '1')
			->setHtmlAttribute('step', '0.01')
			->addRule(Form::Float, 'Rychlost učení musí být číslo')
			->addRule(Form::Range, 'Rychlost učení musí být mezi 0 a 1', [0, 1])
			->setDefaultValue(0.9)
			->setOption('description', 'Určuje, jak moc se váhy neuronů přizpůsobují na začátku trénování. Vyšší hodnota znamená rychlejší počáteční učení. (Rozmezí: 0.0 - 1.0)');

		$form->addText('min_learning_rate', 'Koncová rychlost učení')
			->setRequired('Vyplňte minimální rychlost učení')
			->setHtmlAttribute('type', 'number')
			->setHtmlAttribute('min', '0.001')
			->setHtmlAttribute('max', '1')
			->setHtmlAttribute('step', '0.001')
			->addRule(Form::Float, 'Minimální rychlost učení musí být číslo')
			->addRule(Form::Range, 'Minimální rychlost učení musí být mezi 0 a 1', [0, 1])
			->setDefaultValue(0.1)
			->setOption('description', 'Minimální hodnota rychlosti učení, na kterou klesne během trénování. (Rozmezí: 0.0 - 1.0)');

		$form->addText('radius', 'Počáteční poloměr okolí')
			->setHtmlAttribute('type', 'number')
			->setHtmlAttribute('min', '0')
			->setHtmlAttribute('max', '100')
			->setHtmlAttribute('step', '1')
			->addRule(Form::Float, 'Poloměr musí být číslo')
			->addRule(Form::Range, 'Poloměr musí být mezi 0 a 100', [0, 100])
			->setNullable()
			->setOption('description', 'Definuje velikost oblasti neuronů, které jsou aktualizovány spolu s vítězným neuronem na začátku. Větší poloměr ovlivňuje více neuronů. (Rozmezí: 0 - 100). Pokud není zadán, je automaticky použita polovina rozměru mapy R = m/2');

		$form->addText('min_radius', 'Koncový poloměr okolí')
			->setRequired('Vyplňte minimální poloměr')
			->setHtmlAttribute('type', 'number')
			->setHtmlAttribute('min', '0')
			->setHtmlAttribute('max', '100')
			->setHtmlAttribute('step', '0.1')
			->addRule(Form::Float, 'Minimální poloměr musí být číslo')
			->addRule(Form::Range, 'Minimální poloměr musí být mezi 0 a 100', [0, 100])
			->setDefaultValue(1.0)
			->setOption('description', 'Minimální hodnota poloměru okolí. (Rozmezí: 0 - 100, doporučená výchozí hodnota 1.0)');

		$form->addText('num_batches', 'Počet sekcí rozdělení vstupního souboru')
			->setRequired('Vyplňte počet částí rozdělení vstupnního souboru')
			->setHtmlAttribute('type', 'number')
			->setHtmlAttribute('min', '0')
			->setHtmlAttribute('max', '100')
			->setHtmlAttribute('step', '1')
			->addRule(Form::Range, 'Počet sekcí musí být mezi 0 a 100', [0, 100])
			->setDefaultValue(10)
			->setOption('description', 'Rozděluje vstupní data do několika částí (dávek) pro minimalizaci vynechání zpracování části vstupního souboru při použití stochastických přístupů.');

		$form->addText('max_batch_percent', 'Maximální velikost dávky (%)')
			->setRequired('Vyplňte maximální velikost dávky')
			->setHtmlAttribute('type', 'number')
			->setHtmlAttribute('min', '0')
			->setHtmlAttribute('max', '100')
			->setHtmlAttribute('step', '0.01')
			->addRule(Form::Float, 'Maximální velikost dávky musí být číslo')
			->addRule(Form::Range, 'Maximální velikost dávky musí být mezi 0 a 100', [0, 100])
			->setDefaultValue(5.0)
			->setOption('description', 'Maximální procentuální velikost jedné dávky dat z celého vstupního souboru. (Rozmezí: 0% - 100%). Koncová hodnota ke které cílí křivka vývoje počtu zpracovaných vstupních vektorů na jeden průchod.');

		$form->addText('min_batch_percent', 'Minimální velikost dávky (%)')
			->setRequired('Vyplňte minimální velikost dávky')
			->setHtmlAttribute('type', 'number')
			->setHtmlAttribute('min', '0')
			->setHtmlAttribute('max', '100')
			->setHtmlAttribute('step', '0.01')
			->addRule(Form::Float, 'Minimální velikost dávky musí být číslo')
			->addRule(Form::Range, 'Minimální velikost dávky musí být mezi 0 a 100', [0, 100])
			->setDefaultValue(0.1)
			->setOption('description', 'Minimální procentuální velikost jedné dávky dat z celého vstupního souboru. (Rozmezí: 0% - 100%). Počáteční hodnota ze které vychází křivka vývoje počtu zpracovaných vstupních vektorů na jeden průchod.');

		$valuesUpdateType = [
			'logarithmic' => 'Logaritmický',
			'linear-growth' => 'Lineární růst',
			'linear-drop' => 'Lineární pokles',
			'exponential' => 'Exponenciální',
			'exp-growth' => 'Exponenciální růst',
			'exp-drop' => 'Exponenciální pokles'
		];

		$form->addSelect('lr_decay_type', 'Typ poklesu rychlosti učení', $valuesUpdateType)
			->setHtmlAttribute('class', 'form-select')
			->setRequired('Vyberte typ poklesu rychlosti učení')
			->setDefaultValue('linear-drop')
			->setOption('description', 'Metoda, jakou se snižuje rychlost učení během trénování (např. lineární, exponenciální).');

		$form->addSelect('radius_decay_type', 'Typ poklesu poloměru', $valuesUpdateType)
			->setHtmlAttribute('class', 'form-select')
			->setRequired('Vyberte typ poklesu poloměru')
			->setDefaultValue('linear-drop')
			->setOption('description', 'Metoda, jakou se snižuje poloměr okolí během trénování.');

		$form->addSelect('batch_growth_type', 'Typ růstu dávky', $valuesUpdateType)
			->setHtmlAttribute('class', 'form-select')
			->setRequired('Vyberte typ růstu dávky')
			->setDefaultValue('exp-growth')
			->setOption('description', 'Metoda, jakou se případně mění velikost dávky během trénování (relevantní pro některé strategie).');

		$form->addText('random_seed', 'Random seed')
			->setHtmlAttribute('type', 'number')
			->setHtmlAttribute('min', '0')
			->setHtmlAttribute('max', '1000')
			->setHtmlAttribute('step', '1')
			->addRule(Form::Range, 'Random seed musí být mezi 0 a 1000', [0, 1000])
			->setNullable()
			->setOption('description', 'Číslo pro inicializaci generátoru náhodných čísel. Umožňuje reprodukovatelnost výsledků. ');

		$form->addSelect('growth_g', 'Růst G', [
			1 => '1',
			5 => '5',
			15 => '15',
			25 => '25',
			50 => '50',
			100 => '100'
		])
			->setHtmlAttribute('class', 'form-select')
			->setRequired('Vyberte hodnotu růstu G')
			->setPrompt('Vyberte hodnotu')
			->setOption('description', 'Parametr ovlivňující dynamiku růstu/poklesu parametrů (např. rychlosti učení, poloměru). Konkrétní význam závisí na zvoleném typu poklesu/růstu.');

		$form->addSelect('map_size', 'Velikost mapy', [
			'10x10' => '10x10',
			'20x20' => '20x20',
			'30x30' => '30x30'
		])
			->setRequired('Vyberte velikost mapy')
			->setDefaultValue('20x20')
			->setOption('description', 'Rozměry mřížky neuronů (např. 10x10, 20x20).');

		$form->addText('epoch_multiplier', 'Násobitel epoch')
			->setRequired('Vyplňte násobitel epoch')
			->setHtmlAttribute('type', 'number')
			->setHtmlAttribute('min', '0')
			->setHtmlAttribute('max', '10000')
			->setHtmlAttribute('step', '0.5')
			->addRule(Form::Range, 'Násobitel epoch musí být mezi 0 a 10000', [0, 10000])
			->setDefaultValue(1)
			->setOption('description', 'Násobitel, kolikrát se má projít celý dataset nad rámec základního počtu epoch, který je roven počtu vstupních vektorů datasetu. [0,10000]');

		$form->addText('min_q_error', 'Minimální chyba Q')
			->setHtmlAttribute('type', 'number')
			->setHtmlAttribute('min', '0')
			->setHtmlAttribute('max', '1')
			->setHtmlAttribute('step', '0.01')
			->addRule(Form::Float, 'Minimální chyba Q musí být číslo')
			->addRule(Form::Range, 'Minimální chyba Q musí být mezi 0 a 1', [0, 1])
			->setOption('description', 'Pokud je nastavena, trénování se může zastavit, pokud průměrná vzdálenost datových bodů od jejich nejbližších neuronů klesne pod tuto hodnotu. (Rozmezí: 0.0 - 1.0)');

		$form->addSelect('map_type', 'Typ mapy', [
			'square' => 'Čtvercová',
			'hex' => 'Hexagonální'
		])
			->setRequired('Vyberte typ mapy')
			->setDefaultValue('square')
			->setOption('description', 'Struktura sousedství neuronů (Čtvercová / Hexagonální). Hexagonální má rovnoměrnější pokrytí.');

		$form->addSelect('normalize_weights_flag', 'Normalizovat váhy', [
				0	=> "Ne", 1	=> "Ano"
			])
			->setRequired('Vyberte')
			->setOption('description', 'Určuje, zda se mají váhy neuronů normalizovat (na jednotkovou délku) po každé aktualizaci. (Ano/Ne)');

		$form->addText('max_epochs_without_improvement', 'Maximální počet epoch bez zlepšení')
			->setHtmlAttribute('type', 'number')
			->setHtmlAttribute('min', '0')
			->setHtmlAttribute('max', '1000')
			->setHtmlAttribute('step', '1')
			->addRule(Form::Range, 'Maximální počet epoch bez zlepšení musí být mezi 0 a 1000', [0, 1000])
			->setOption('description', 'Pokud je nastaveno, trénování se zastaví, pokud se chyba Q nezlepší po zadaný počet epoch. (Rozmezí: 0 - 1000)');

		$form->addSubmit('submit', 'Uložit nastavení SOM');

		$form->onValidate[] = function (Form $form, ArrayHash $values): void {
			// form validation
		};

		$form->onSuccess[] = function (Form $form, ArrayHash $values) use ($onSuccess): void {
			$project_id = $this->projectsService->saveProjectSomSettings($values);
			$onSuccess($project_id);
		};

		return $form;
	}
}