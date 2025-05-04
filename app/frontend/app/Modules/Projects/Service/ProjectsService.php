<?php

declare(strict_types=1);

namespace App\Modules\Projects\Service;

use App\Common\Service\BaseService;
use App\Common\Service\BaseCrudServiceTrait;
use App\Modules\Projects\Repository\ProjectsRepository;
use Dibi\Result;
use Dibi\Row;
use Nette\Http\FileUpload;
use Nette\Utils\ArrayHash;

class ProjectsService extends BaseService
{
    use BaseCrudServiceTrait;

    private ProjectsRepository $projectsRepository;

    public function __construct(ProjectsRepository $projectsRepository)
    {
        $this->projectsRepository = $projectsRepository;
    }

    public function getProjects(int $customer_id)
    {
        return $this->projectsRepository->getProjectsForCustomer($customer_id);
    }

	public function getProjectDetail(int $customer_id, int $project_id): ?Row
	{
		$projectDetail = $this->projectsRepository->getProjectDetail($customer_id, $project_id);
		return $projectDetail ? $this->prepareProject($projectDetail) : null;
	}

	private function prepareProject(Row $project)
	{
		$project->som_settings 		= empty($project->som_settings) ? null : json_decode($project->som_settings);
		$project->project_settings	= empty($project->project_settings) ? null : json_decode($project->project_settings);

		return $project;
	}

	public function createProject(array|ArrayHash $data): int
	{
		$projectData = $this->prepareProjectForDb($data);
		$input_csv = $data['input_csv'] ?? null;

		$projectId = $this->projectsRepository->create($projectData);

		$this->uploadInputCsv($input_csv, $projectData);
		return $projectId;
	}

	private function uploadInputCsv(FileUpload $input_csv, array|ArrayHash $projectData): void
	{
		$csvDir = WWW_DIR . '/userFiles/' . $projectData['uid_hash'] . '/csv';
		if (!is_dir($csvDir)) {
			mkdir($csvDir, 0777, true);
		}

		$this->saveInputCsvData($input_csv, $projectData['project_id']);

		$input_csv->move($csvDir.'/input.csv');
	}

	public function saveInputCsvData(FileUpload $input_csv, int $project_id): void
	{
		$file = new \SplFileObject($input_csv->getTemporaryFile());
		$file->setFlags(\SplFileObject::READ_CSV);

		$file->rewind();
		$header = $file->current();
		$file->seek(PHP_INT_MAX);

		$csvData = [
			'column_count' => count($header),
			'column_names' => implode(',', array_map('trim', $header)),
			'row_count' => $file->key() - 1,
			'project_id' => $project_id,
			'file_size' => round($input_csv->getSize() / 1024 / 1024, 2),
		];

		$this->projectsRepository->saveInputFileData($csvData);
	}

	public function saveProject(array|ArrayHash $data): int
	{
		return $this->saveWithTransaction(
			$data,
			$this->projectsRepository,
			fn($data) => $this->prepareProjectForDb($data)
		);
	}

	public function saveProjectSettings(array|ArrayHash $data): int
	{
		$project_id = intval($data->project_id);
		unset($data->project_id);
		$projectJsonData = json_encode($data);

		$this->projectsRepository->updateProjectSettings($project_id, $this->getCustomerId(), $projectJsonData);

		return $project_id;
	}

	public function saveProjectSomSettings(array|ArrayHash $data): int
	{
		$project_id = intval($data->project_id);
		unset($data->project_id);
		$somJsonData = json_encode($data);

		$this->projectsRepository->updateProjectSomSettings($project_id, $this->getCustomerId(), $somJsonData);

		return $project_id;
	}

	private function prepareProjectForDb(array|ArrayHash $data): array
	{
		return [
			'project_id'	=> intval($data['project_id']) ?: $this->projectsRepository->getNewId(),
			'uid_hash'		=> $this->getUid(),
			'name'			=> $data->name,
			'customer_id'	=> $this->getCustomerId(),
			'som_settings'	=> json_encode([]),
		];
	}

	public function deleteProject(int $customer_id, Row $project): Result|int|null
	{
		if ($project->customer_id !== $customer_id) {
			throw new \Exception('Tento zákazník nemá oprávnění k odstranění tohoto projektu.');
		}

		return $this->delete(
			$this->projectsRepository,
			$project->project_id
		);
	}

	public function submitProject(int $customer_id, Row $project): Result|int|null
	{
		if ($project->customer_id !== $customer_id) {
			throw new \Exception('Tento zákazník nemá oprávnění k odstranění tohoto projektu.');
		}

		return $this->projectsRepository->submitProjectToAnalyze($project->project_id, $customer_id);
	}

	public function getProjectFiles(int $customer_id, string $uid_hash, ?string $type = null): array
	{
		if ($type === null) {
			return [
				'visualization' => $this->getProjectVisualizations($customer_id, $uid_hash),
				'csv' => $this->getProjectCsvFiles($customer_id, $uid_hash),
				'json' => $this->getProjectJsonFiles($customer_id, $uid_hash),
			];
		}
		switch ($type) {
			case 'csv':
				return ['csv' => $this->getProjectCsvFiles($customer_id, $uid_hash)];
				break;
			case 'json':
				return ['json' => $this->getProjectJsonFiles($customer_id, $uid_hash)];
				break;
			case 'visualization':
				return ['visualization' => $this->getProjectVisualizations($customer_id, $uid_hash)];
				break;
			default:
				throw new \Exception('Neplatný typ souboru.');
		}
	}

	private function getProjectVisualizations(int $customer_id, string $uid_hash): array
	{
		$visualizationDir = WWW_DIR . '/userFiles/' . $uid_hash . '/visualization';
		if (!is_dir($visualizationDir)) {
			return [];
		}

		$files = scandir($visualizationDir);
		$visualizations = [];
		foreach ($files as $file) {
			if ($file === '.' || $file === '..') {
				continue;
			}
			$prefix = explode('_', $file)[0];
			$visualizations[$prefix][] = $file;
		}

		krsort($visualizations);
		return $visualizations;
	}

	private function getProjectCsvFiles(int $customer_id, string $uid_hash): array
	{
		$csvDir = WWW_DIR . '/userFiles/' . $uid_hash . '/csv';
		if (!is_dir($csvDir)) {
			return [];
		}

		$files = scandir($csvDir);
		$csvFiles = [];
		foreach ($files as $file) {
			if ($file === '.' || $file === '..') {
				continue;
			}
			$csvFiles[] = $file;
		}

		return $csvFiles;
	}

	private function getProjectJsonFiles(int $customer_id, string $uid_hash): array
	{
		$jsonDir = WWW_DIR . '/userFiles/' . $uid_hash . '/json';
		if (!is_dir($jsonDir)) {
			return [];
		}

		$files = scandir($jsonDir);
		$jsonFiles = [];
		foreach ($files as $file) {
			if ($file === '.' || $file === '..') {
				continue;
			}
			$jsonFiles[] = $file;
		}

		return $jsonFiles;
	}

	public function getProjectConfig($projectDetail): array
	{
		$defaultConfig = $this->getDefaultConfig();
		// Získání uložených nastavení z projectDetail
		$savedConfig = [];
		if (!empty($projectDetail->som_settings)) {
			$savedConfig = (array)$projectDetail->som_settings;
		}

		// Spojení výchozích a uložených nastavení
		$config = array_merge($defaultConfig, $savedConfig);

		return $config;
	}

	private function getDefaultConfig(): array
	{
		// Výchozí hodnoty z KohonenSOM.__init__
		return [
			'learning_rate' => 0.9,
			'min_learning_rate' => 0.1,
			'radius' => null,
			'min_radius' => 0.1,
			'num_batches' => 10,
			'min_batch_percent' => 0.1,
			'max_batch_percent' => 5,
			'lr_decay_type' => 'exp-drop',
			'radius_decay_type' => 'exp-drop',
			'batch_growth_type' => 'exp-growth',
			'random_seed' => null,
			'growth_g' => 15.0,
			'normalize_weights_flag' => false,
			'epoch_multiplier' => 1.0,
			'map_type' => 'hex',
			'min_q_error' => null,
			'max_epochs_without_improvement' => null
		];
	}

	public function getConfigDescription(): array
	{
		return [
			'm' => 'Počet řádků mapy',
			'n' => 'Počet sloupců mapy',
			'learning_rate' => 'Výchozí hodnota pro učení',
			'min_learning_rate' => 'Minimální hodnota pro učení',
			'radius' => 'Poloměr sítě',
			'min_radius' => 'Minimální poloměr sítě',
			'num_batches' => 'Počet batchů',
			'min_batch_percent' => 'Minimální procento batchů',
			'max_batch_percent' => 'Maximální procento batchů',
			'lr_decay_type' => 'Typ útlumu učení',
			'radius_decay_type' => 'Typ útlumu poloměru',
			'batch_growth_type' => 'Typ růstu batchů',
			'random_seed' => 'Náhodné číslo',
			'growth_g' => 'Koeficient růstu',
			'normalize_weights_flag' => 'Normalizovat váhy',
			'epoch_multiplier' => 'Koeficient násobení epoch',
			'map_type' => 'Typ mapy',
			'min_q_error' => 'Minimální kvantizační chyba',
			'max_epochs_without_improvement' => 'Maximální počet epoch bez zlepšení',
		];
	}

	public function getConfigSelectValues(): array
	{
		return [
			'lr_decay_type' => ['exp-drop', 'exp-inc', 'linear-drop', 'linear-inc'],
			'radius_decay_type' => ['exp-drop', 'exp-inc', 'linear-drop', 'linear-inc'],
			'batch_growth_type' => ['exp-growth', 'linear-growth'],
			'map_type' => ['hex', 'rect'],
			'lr_decay_type' => ['exp-drop', 'exp-inc', 'linear-drop', 'linear-inc'],
			'radius_decay_type' => ['exp-drop', 'exp-inc', 'linear-drop', 'linear-inc'],
			'batch_growth_type' => ['exp-growth', 'linear-growth'],
			'map_size' => ['10x10', '20x20', '30x30'],
		];
	}

	public function getProjectConfigDescription(): array
	{
		return [
			"selected_columns"		=> "Vybrané sloupce pro analýzu",
			"categorical_column"	=> "Kategorický sloupec",
			"primary_id"			=> "Hlavní ID",
			"analysis_columns"		=> "Sloupce pro analýzu",
			"legend_column"			=> "Sloupec pro legendu",
			"legend_title"			=> "Název legendy"
		];
	}

	public function getInputFileColumns(int $project_id): array
	{
		$projectInputFileData = $this->getInputFileData($project_id);

		return $projectInputFileData['column_names'];
	}

	public function getInputFileData(int $project_id): Row
	{
		$fileData = $this->projectsRepository->getInputFileData($project_id);

		if (! empty($fileData['column_names'])) {
			$fileData['column_names'] = explode(',', $fileData['column_names']);
			$fileData['column_names'] = array_combine($fileData['column_names'],$fileData['column_names']);
		}

		return $fileData;
	}
}
