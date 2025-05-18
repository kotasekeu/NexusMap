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

/**
 * Service class for handling project-related operations
 */
class ProjectsService extends BaseService
{
    use BaseCrudServiceTrait;

    private ProjectsRepository $projectsRepository;

    /**
     * @param ProjectsRepository $projectsRepository
     */
    public function __construct(ProjectsRepository $projectsRepository)
    {
        $this->projectsRepository = $projectsRepository;
    }

    /**
     * Get all projects for a specific customer
     * 
     * @param int $customer_id The ID of the customer
     * @return array Array of prepared project data
     */
    public function getProjects(int $customer_id)
    {
		$projects = $this->projectsRepository->getProjectsForCustomer($customer_id);

		return $this->prepareProjects($projects);
    }

    /**
     * Prepare multiple projects for output
     * 
     * @param array $projects Array of project data
     * @return array Array of prepared projects
     */
	private function prepareProjects(array $projects): array
	{
		$returnProjects = [];

		if (empty($projects)) {
			return $returnProjects;
		}

		foreach ($projects as $project) {
			$returnProjects[] = $this->prepareProject($project);
		}

		return $returnProjects;
	}

    /**
     * Get detailed information about a specific project
     * 
     * @param int $customer_id The ID of the customer
     * @param int $project_id The ID of the project
     * @return Row|null Prepared project data or null if not found
     */
	public function getProjectDetail(int $customer_id, int $project_id): ?Row
	{
		$projectDetail = $this->projectsRepository->getProjectDetail($customer_id, $project_id);
		return $projectDetail ? $this->prepareProject($projectDetail) : null;
	}

    /**
     * Prepare a single project for output
     * 
     * @param Row $project Project data row
     * @return Row Prepared project data
     */
	private function prepareProject(Row $project)
	{
		$project->som_settings 		= $this->getSomSettings($project->som_settings);
		$project->project_settings	= empty($project->project_settings) ? null : json_decode($project->project_settings);
		$project->results			= empty($project->results) ? null : json_decode($project->results);

		return $project;
	}

    /**
     * Get SOM settings from JSON string
     * 
     * @param string $som_settings JSON string containing SOM settings
     * @return \stdClass|null Decoded SOM settings or null if empty
     */
	private function getSomSettings(string $som_settings) : ?\stdClass
	{
		if (empty($som_settings) || $som_settings == '') {
			return null;
		}

		$returnData = json_decode($som_settings);

		if (isset($returnData->map_size)) {
			$mn = explode('x', $returnData->map_size);
			$returnData->m = intval($mn[0]);
			$returnData->n = intval($mn[1]);
			unset($returnData->map_size);
		}

		if (empty($returnData)) {
			return null;
		}

		return $returnData;
	}

    /**
     * Create a new project
     * 
     * @param array|ArrayHash $data Project data
     * @return int ID of the created project
     */
	public function createProject(array|ArrayHash $data): int
	{
		$projectData = $this->prepareProjectForDb($data);
		$input_csv = $data['input_csv'] ?? null;

		$projectId = $this->projectsRepository->create($projectData);
		
		$this->uploadInputCsv($input_csv, $projectData);
		return $projectId;
	}

    /**
     * Clean and validate CSV data
     * 
     * @param FileUpload $input_csv Uploaded CSV file
     * @return array Cleaned CSV data with header and rows
     * @throws \RuntimeException If file cannot be opened or is empty
     */
	private function cleanCsvData(FileUpload $input_csv): array
	{
		$handle = fopen($input_csv->getTemporaryFile(), 'r');
		if ($handle === false) {
			throw new \RuntimeException('Nelze otevřít CSV soubor');
		}

		// Načtení a kontrola BOM
		$firstLine = fgets($handle);
		if ($firstLine === false) {
			fclose($handle);
			throw new \RuntimeException('Prázdný CSV soubor');
		}

		// Odstranění BOM
		$firstLine = ltrim($firstLine, "\xEF\xBB\xBF");
		
		// Zpracování hlavičky
		$header = str_getcsv(trim($firstLine), ',', '"', '\\');
		$header = array_map('trim', $header);
		$headerCount = count($header);
		
		// Načtení a očištění dat
		$data = [];
		$rowCount = 0;
		
		while (($row = fgetcsv($handle, 0, ',', '"', '\\')) !== false) {
			// Přeskočit prázdné řádky
			if (count($row) === $headerCount && array_filter($row, 'strlen')) {
				$data[] = $row;
				$rowCount++;
			}
		}
		
		fclose($handle);
		return [
			'header' => $header,
			'data' => $data,
			'row_count' => $rowCount
		];
	}

    /**
     * Save input CSV data to database
     * 
     * @param FileUpload $input_csv Uploaded CSV file
     * @param int $project_id ID of the project
     * @return void
     */
	public function saveInputCsvData(FileUpload $input_csv, int $project_id): void
	{
		$cleanedData = $this->cleanCsvData($input_csv);

		$csvData = [
			'column_count' => count($cleanedData['header']),
			'column_names' => implode(',', $cleanedData['header']),
			'row_count' => $cleanedData['row_count'],
			'project_id' => $project_id,
			'file_size' => round($input_csv->getSize() / 1024 / 1024, 2),
		];

		$this->projectsRepository->saveInputFileData($csvData);
	}

    /**
     * Upload and process input CSV file
     * 
     * @param FileUpload $input_csv Uploaded CSV file
     * @param array|ArrayHash $projectData Project data
     * @return void
     * @throws \RuntimeException If file operations fail
     */
	private function uploadInputCsv(FileUpload $input_csv, array|ArrayHash $projectData): void
	{
		if ($this->getCustomerType() == "basic") {

		}
		$csvDir = WWW_DIR . '/userFiles/' . $projectData['uid_hash'] . '/csv';
		if (!is_dir($csvDir)) {
			mkdir($csvDir, 0777, true);
		}
		
		// Nejdřív zpracujeme data pro databázi
		$this->saveInputCsvData($input_csv, $projectData['project_id']);

		// Získáme vyčištěná data
		$cleanedData = $this->cleanCsvData($input_csv);
		
		// Uložíme vyčištěný soubor
		$handle = fopen($csvDir.'/input.csv', 'w');
		if ($handle === false) {
			throw new \RuntimeException('Nelze vytvořit výstupní CSV soubor');
		}

		// Zápis hlavičky a dat
		fputcsv($handle, $cleanedData['header'], ',', '"', '\\');
		foreach ($cleanedData['data'] as $row) {
			fputcsv($handle, $row, ',', '"', '\\');
		}
		
		$stat = fstat($handle);
		ftruncate($handle, $stat['size']-1);
		
		fclose($handle);
	}

    /**
     * Save project data
     * 
     * @param array|ArrayHash $data Project data
     * @return int ID of the saved project
     */
	public function saveProject(array|ArrayHash $data): int
	{
		return $this->saveWithTransaction(
			$data,
			$this->projectsRepository,
			fn($data) => $this->prepareProjectForDb($data)
		);
	}

    /**
     * Save project settings
     * 
     * @param array|ArrayHash $data Project settings data
     * @return int ID of the project
     */
	public function saveProjectSettings(array|ArrayHash $data): int
	{
		$project_id = intval($data->project_id);
		unset($data->project_id);
		$projectJsonData = json_encode($data);

		$this->projectsRepository->updateProjectSettings($project_id, $this->getCustomerId(), $projectJsonData);

		return $project_id;
	}

    /**
     * Save SOM settings for a project
     * 
     * @param array|ArrayHash $data SOM settings data
     * @return int ID of the project
     */
	public function saveProjectSomSettings(array|ArrayHash $data): int
	{
		$project_id = intval($data->project_id);
		unset($data->project_id);

		foreach ($data as $key => $value) {
			if (empty($value) || $value == '') {
				unset($data->$key);
			}
		}

		if (isset($data->map_size)) {
			$mn = explode('x', $data->map_size);
			$data->m = intval($mn[0]);
			$data->n = intval($mn[1]);
			unset($data->map_size);
		}
		$intValFields = ['max_epochs_without_improvement', 'random_seed', 'num_batches', 'project_id'];
		foreach ($intValFields as $value) {
			if (isset($data[$value]) && ! empty($data[$value])) {
				$data[$value] = intval($data[$value]);
			}
		}

		$somJsonData = json_encode($data);
		$this->projectsRepository->updateProjectSomSettings($project_id, $this->getCustomerId(), $somJsonData);

		return $project_id;
	}

    /**
     * Prepare project data for database storage
     * 
     * @param array|ArrayHash $data Project data
     * @return array Prepared project data
     */
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

    /**
     * Get the last line from Kohonen log file
     * 
     * @param string $uid_hash Unique identifier hash
     * @return string Last line of the log file or empty string if file doesn't exist
     */
	public function getLastLineKohonenLogFile(string $uid_hash): string
	{
		$logFile = WWW_DIR . '/userFiles/' . $uid_hash . '/kohonen-log.txt';
		if (!file_exists($logFile)) {
			return '';
		}

		$handle = fopen($logFile, 'r');
		if ($handle === false) {
			return '';
		}

		$lastLine = '';
		while (($line = fgets($handle)) !== false) {
			$lastLine = $line;
		}
		fclose($handle);

		return trim($lastLine);
	}

    /**
     * Delete a project
     * 
     * @param int $customer_id ID of the customer
     * @param Row $project Project data
     * @return Result|int|null Result of deletion operation
     * @throws \Exception If customer doesn't have permission
     */
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

    /**
     * Submit project for analysis
     * 
     * @param int $customer_id ID of the customer
     * @param Row $project Project data
     * @return Result|int|null Result of submission
     * @throws \Exception If customer doesn't have permission
     */
	public function submitProject(int $customer_id, Row $project): Result|int|null
	{
		if ($project->customer_id !== $customer_id) {
			throw new \Exception('Tento zákazník nemá oprávnění k odstranění tohoto projektu.');
		}

		return $this->projectsRepository->submitProjectToAnalyze($project->project_id, $customer_id);
	}

    /**
     * Get project files by type
     * 
     * @param int $customer_id ID of the customer
     * @param string $uid_hash Unique identifier hash
     * @param string|null $type Type of files to retrieve
     * @return array Array of project files
     * @throws \Exception If invalid file type is specified
     */
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

    /**
     * Scan directory for files
     * 
     * @param string $directory Directory path to scan
     * @return array Array of file names
     */
	private function scanDirectoryForFiles(string $directory): array
	{
		if (!is_dir($directory)) {
			return [];
		}

		$files = scandir($directory);
		$result = [];
		foreach ($files as $file) {
			$fullPath = $directory . '/' . $file;
			if ($file === '.' || $file === '..' || $file[0] === '.' || is_dir($fullPath)) {
				continue;
			}
			$result[] = $file;
		}

		return $result;
	}

    /**
     * Get project visualizations
     * 
     * @param int $customer_id ID of the customer
     * @param string $uid_hash Unique identifier hash
     * @return array Array of visualization files
     */
	private function getProjectVisualizations(int $customer_id, string $uid_hash): array
	{
		$visualizationDir = WWW_DIR . '/userFiles/' . $uid_hash . '/visualization';
		$files = $this->scanDirectoryForFiles($visualizationDir);
		
		$visualizations = [];
		foreach ($files as $file) {
			$prefix = explode('.', $file)[0];
			$visualizations[$prefix][] = $file;
		}

		krsort($visualizations);
		return $visualizations;
	}

    /**
     * Get project CSV files
     * 
     * @param int $customer_id ID of the customer
     * @param string $uid_hash Unique identifier hash
     * @return array Array of CSV files
     */
	private function getProjectCsvFiles(int $customer_id, string $uid_hash): array
	{
		$csvDir = WWW_DIR . '/userFiles/' . $uid_hash . '/csv';
		return $this->scanDirectoryForFiles($csvDir);
	}

    /**
     * Get project JSON files
     * 
     * @param int $customer_id ID of the customer
     * @param string $uid_hash Unique identifier hash
     * @return array Array of JSON files
     */
	private function getProjectJsonFiles(int $customer_id, string $uid_hash): array
	{
		$jsonDir = WWW_DIR . '/userFiles/' . $uid_hash . '/json';
		return $this->scanDirectoryForFiles($jsonDir);
	}

    /**
     * Get project configuration
     * 
     * @param mixed $projectDetail Project detail data
     * @return array Project configuration
     */
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

    /**
     * Get default configuration
     * 
     * @return array Default configuration values
     */
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

    /**
     * Get configuration descriptions
     * 
     * @return array Array of configuration descriptions
     */
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

    /**
     * Get project configuration descriptions
     * 
     * @return array Array of project configuration descriptions
     */
	public function getProjectConfigDescription(): array
	{
		return [
			"selected_columns"		=> "Načtené sloupce z CSV",
			"categorical_column"	=> "Kategorické sloupce",
			"primary_id"			=> "Hlavní ID",
			"analysis_columns"		=> "Sloupce pro numerickou analýzu",
			"segmentation_column"	=> "Sloupec pro segmentaci dat",
			"numerical_column"		=> "Numerické sloupce",
			"string_column"			=> "Textové sloupce",
			"std_threshold"			=> "Prahová hodnota pro extrémní hodnoty",
		];
	}

    /**
     * Get input file columns
     * 
     * @param int $project_id ID of the project
     * @return array Array of column names
     */
	public function getInputFileColumns(int $project_id): array
	{
		$projectInputFileData = $this->getInputFileData($project_id);

		return $projectInputFileData['column_names'];
	}

    /**
     * Get input file data
     * 
     * @param int $project_id ID of the project
     * @return Row Input file data
     */
	public function getInputFileData(int $project_id): Row
	{
		$fileData = $this->projectsRepository->getInputFileData($project_id);

		if (! empty($fileData['column_names'])) {
			$fileData['column_names'] = explode(',', $fileData['column_names']);
			$fileData['column_names'] = array_combine($fileData['column_names'],$fileData['column_names']);
		}

		return $fileData;
	}

    /**
     * Get clusters data
     * 
     * @param string $uid_hash Unique identifier hash
     * @param string|null $cell Cell identifier
     * @return array|null Clusters data or null if file doesn't exist
     */
	public function getClustersData(string $uid_hash, ?string $cell = null): ?array
	{
		$clustersJson = WWW_DIR . '/userFiles/' . $uid_hash . '/json/clusters.json';
		if (!file_exists($clustersJson)) {
			return null;
		}
		$jsonData = file_get_contents($clustersJson);

		$clustersData = json_decode($jsonData, true);
		ksort($clustersData);

		if (! empty($cell)) {
			if (! isset($clustersData[$cell])) {
				return [];
			}
			return [$cell => $clustersData[$cell]];
		}

		return $clustersData;
	}

    /**
     * Get extremes data
     * 
     * @param string $uid_hash Unique identifier hash
     * @param string|null $cell Cell identifier
     * @return array|null Extremes data or null if file doesn't exist
     */
	public function getExtremesData(string $uid_hash, ?string $cell = null): ?array
	{
		$extremesJson = WWW_DIR . '/userFiles/' . $uid_hash . '/json/extremes.json';
		if (!file_exists($extremesJson)) {
			return null;
		}
		$jsonData = file_get_contents($extremesJson);

		$extremesData = json_decode($jsonData, true);
		ksort($extremesData['by_cluster']);
		ksort($extremesData['by_group']);

		if (! empty($cell)) {
			if (! isset($extremesData['by_cluster'][$cell])) {
				return [];
			}
			return [$cell => $extremesData['by_cluster'][$cell]];
		}

		return $extremesData;
	}

    /**
     * Get quantization error data
     * 
     * @param string $uid_hash Unique identifier hash
     * @return array|null Quantization error data or null if file doesn't exist
     */
	public function getQuantizationError(string $uid_hash): ?array
	{
		$qErrorJson = WWW_DIR . '/userFiles/' . $uid_hash . '/json/quantization_error.json';
		if (!file_exists($qErrorJson)) {
			return null;
		}
		$jsonData = file_get_contents($qErrorJson);

		$qErrorData = json_decode($jsonData, true);

		return $qErrorData;
	}

    /**
     * Get records data
     * 
     * @param string $uid_hash Unique identifier hash
     * @param string $primary_id Primary identifier
     * @return array|null Records data or null if file doesn't exist
     */
	public function getRecordsData(string $uid_hash, string $primary_id): ?array
	{
		$csvFile = WWW_DIR . '/userFiles/' . $uid_hash . '/csv/input.csv';
		if (!file_exists($csvFile)) {
			return null;
		}


		$handle = fopen($csvFile, 'r');
		$line = fgets($handle);
		$line = ltrim($line, "\xEF\xBB\xBF\x00..\x1F");

		$headers = str_getcsv(trim($line), ",", '"', '\\');

		$primaryIdIndex = array_search($primary_id, $headers);
		if ($primaryIdIndex === false) {
			fclose($handle);
			return null;
		}

		$records = [];
		while (($row = fgetcsv($handle, 0, ",", '"', '\\')) !== false) {
			if (count($row) === count($headers)) {
				$records[$row[$primaryIdIndex]] = array_combine($headers, $row);
			}
		}

		fclose($handle);
		return $records;
	}

    /**
     * Get statistics data from various sources
     * 
     * @param array $clusters Clusters data
     * @param array $extremes Extremes data
     * @param array $records Records data
     * @param Row $projectDetail Project detail data
     * @return array Statistics data
     */
	public function getStatsDataFromSources($clusters, $extremes, $records, $projectDetail): array
	{
		$clustersWithData = [];
		$categorical_column = $projectDetail->project_settings->categorical_column ?? [];
		$numerical_column = $projectDetail->project_settings->numerical_column ?? [];

		foreach ($clusters as $clusterKey => $cluster) {

			$clustersWithData[$clusterKey] = [
				'count' => count($cluster),
				'numerical_stats' => [],
				'categorical_stats' => [],
				'records' => [],
				'extremes' => []
			];

			// Zpracování numerických sloupců
			foreach ($numerical_column as $column) {
				$values = [];
				foreach ($cluster as $recordId) {
					if (isset($records[$recordId][$column]) && $records[$recordId][$column] !== '') {
						$values[] = floatval($records[$recordId][$column]);
					}
				}

				if (!empty($values)) {
					$clustersWithData[$clusterKey]['numerical_stats'][$column] = [
						'min' => min($values),
						'max' => max($values),
						'avg' => array_sum($values) / count($values),
						'median' => $this->calculateMedian($values)
					];
				}
			}

			// Zpracování kategorických sloupců
			foreach ($categorical_column as $column) {
				$categories = [];
				foreach ($cluster as $recordId) {
					if (isset($records[$recordId][$column])) {
						$value = $records[$recordId][$column];
						if (!isset($categories[$value])) {
							$categories[$value] = 0;
						}
						$categories[$value]++;
					}
				}
				$clustersWithData[$clusterKey]['categorical_stats'][$column] = $categories;
			}

			// Zpracování záznamů
			foreach ($cluster as $recordId) {
				if (! isset($records[$recordId])) {
					continue;
				}

				$clustersWithData[$clusterKey]['records'][$recordId] = $records[$recordId];
			}

			// Zpracování extrémů
			if (isset($extremes['by_cluster'][$clusterKey])) {
				foreach ($extremes['by_cluster'][$clusterKey] as $extremeRecordId) {
					$clustersWithData[$clusterKey]['extremes'][$extremeRecordId] = $records[$extremeRecordId];
				}
			}
		}

		return $clustersWithData;
	}

    /**
     * Get statistics data from sources for map
     * 
     * @param array $clusters Clusters data
     * @param array $extremes Extremes data
     * @param array $records Records data
     * @param Row $projectDetail Project detail data
     * @return array Statistics data for map
     */
	public function getStatsDataFromSourcesForMap($clusters, $extremes, $records, $projectDetail): array
	{
		$clustersWithData = [];
		$numerical_column = $projectDetail->project_settings->numerical_column ?? [];

		foreach ($clusters as $clusterKey => $cluster) {
			$clustersWithData[$clusterKey] = [
				'numerical_stats'	=> [],
				'records_counts'	=> count($cluster),
				'extremes_counts'	=> 0
			];

			// Zpracování numerických sloupců
			foreach ($numerical_column as $column) {
				$values = [];
				foreach ($cluster as $recordId) {
					if (isset($records[$recordId][$column]) && $records[$recordId][$column] !== '') {
						$values[] = floatval($records[$recordId][$column]);
					}
				}

				if (!empty($values)) {
					$clustersWithData[$clusterKey]['numerical_stats'][$column] = array_sum($values) / count($values);
				}
			}

			// Zpracování extrémů
			if (isset($extremes['by_cluster'][$clusterKey])) {
				foreach ($extremes['by_cluster'][$clusterKey] as $extremeRecordId) {
					$clustersWithData[$clusterKey]['extremes_counts']++;
				}
			}
		}

		return $clustersWithData;
	}

    /**
     * Get cell data
     * 
     * @param Row $projectDetail Project detail data
     * @param string $cell_id Cell identifier
     * @return array|null Cell data or null if no data available
     */
	public function getCellData(Row $projectDetail, string $cell_id): ?array
	{
		$clusters = $this->getClustersData($projectDetail->uid_hash, $cell_id);
		$extremes	= $this->getExtremesData($projectDetail->uid_hash, $cell_id);
		$records	= $this->getRecordsData($projectDetail->uid_hash, $projectDetail->project_settings->primary_id);
		$numerical_column = $projectDetail->project_settings->numerical_column ?? [];

		if (empty($records) || empty($clusters)) {
			return null;
		}

		$returnData = [
			'extremes'			=> [],
			'records'			=> [],
			'numerical_stats'	=> []
		];
		foreach ($clusters as $clusterKey => $cluster) {
			foreach ($cluster as $recordId) {
				if (isset($records[$recordId])) {
					$returnData['records'][$recordId] = $records[$recordId];
				}
			}
		}

		foreach ($extremes as $extremeKey => $extreme) {
			foreach ($extreme as $recordId) {
				if (isset($records[$recordId])) {
					$returnData['extremes'][$recordId] = $records[$recordId];
				}
			}
		}

		// Zpracování numerických sloupců
		if (! empty($numerical_column)) {
			foreach ($clusters as $clusterKey => $cluster) {
				foreach ($numerical_column as $column) {
					$values = [];
					foreach ($cluster as $recordId) {
						if (isset($records[$recordId][$column]) && $records[$recordId][$column] !== '') {
							$values[] = floatval($records[$recordId][$column]);
						}
					}

					if (!empty($values)) {
						$returnData['numerical_stats'][$column] = [
							'min' => min($values),
							'max' => max($values),
							'avg' => round(array_sum($values) / count($values), 2),
							'median' => $this->calculateMedian($values)
						];
					}
				}
			}
		}

		return $returnData;
	}

    /**
     * Get global statistics
     * 
     * @param Row $projectDetail Project detail data
     * @param array $records Records data
     * @return array|null Global statistics or null if no data available
     */
	public function getGlobalStats(Row $projectDetail, array $records): ?array
	{
		$numerical_column = $projectDetail->project_settings->numerical_column ?? [];
		$categorical_column = $projectDetail->project_settings->categorical_column ?? [];

		$numericalStats = [];
		foreach ($numerical_column as $col) {
			$values = array_filter(array_map('floatval', array_column($records, $col)), fn($v) => $v !== null);
			if ($values === []) continue;

			sort($values);
			$count = count($values);
			$median = ($count % 2 === 0)
				? ($values[$count / 2 - 1] + $values[$count / 2]) / 2
				: $values[(int)floor($count / 2)];

			$numericalStats[$col] = [
				'min' => min($values),
				'max' => max($values),
				'avg' => round(array_sum($values) / $count, 3),
				'median' => $median,
			];
		}

		$categoricalStats = [];
		foreach ($categorical_column as $col) {
			$freq = [];
			foreach ($records as $row) {
				$val = $row[$col] ?? null;
				if ($val !== null) {
					$freq[$val] = ($freq[$val] ?? 0) + 1;
				}
			}
			arsort($freq);
			$categoricalStats[$col] = $freq;
		}

		return [
			'numerical' => $numericalStats,
			'categorical' => $categoricalStats,
		];
	}

    /**
     * Calculate median value from array of numbers
     * 
     * @param array $values Array of numeric values
     * @return float Median value
     */
	private function calculateMedian(array $values): float
	{
		sort($values);
		$count = count($values);
		$middle = floor($count / 2);

		if ($count % 2 == 0) {
			return ($values[$middle - 1] + $values[$middle]) / 2;
		}

		return $values[$middle];
	}
}
