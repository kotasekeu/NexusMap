<?php

declare(strict_types=1);

namespace App\Modules\Projects\Repository;

use App\Common\Repository\BaseRepository;
use Dibi\Row;

/**
 * ProjectRepository class
 * 
 * This class extends BaseRepository and provides methods for managing projects.
 */
class ProjectsRepository extends BaseRepository
{
	protected string $table = 'projects';
	protected string $primaryKey = 'project_id';

	protected string $sourceFileTable = 'source_files';
	protected string $targetFilePrimaryKey = 'source_file_id';


	/**
	 * Retrieves all projects for a specific customer.
	 * 
	 * @param int $customer_id Customer ID.
	 * @return array<Row> Array of project rows.
	 */
	public function getProjectsForCustomer(int $customer_id): array
	{
		return $this->db->select('P.*, SF.row_count, SF.column_count, SF.column_names, SF.file_size')
			->from($this->getTable() . " AS P")
			->leftJoin($this->sourceFileTable . " AS SF")
				->on("SF.project_id = P.project_id")
			->where('P.customer_id = %i', $customer_id)
			->where('P.visible = 1')
			->fetchAll();
	}

	/**
	 * Retrieves project details for a specific project and customer.
	 * 
	 * @param int $customer_id Customer ID.
	 * @param int $project_id Project ID.
	 * @return ?Row Project details or null if not found.
	 */
	public function getProjectDetail(int $customer_id, int $project_id): ?Row
	{
		return $this->db->select('P.*, SF.row_count, SF.column_count, SF.column_names, SF.file_size')
			->from($this->getTable() . " AS P")
			->leftJoin($this->sourceFileTable . " AS SF")
			->on("SF.project_id = P.project_id")
			->where('P.customer_id = %i', $customer_id)
			->where('P.project_id = %i', $project_id)
			->where('P.visible = 1')
			->fetch();
	}

	/**
	 * Saves input file data to the database.
	 * 
	 * @param array $fileData Array of file data to be saved.
	 */
	public function saveInputFileData(array $fileData): void
	{
		$this->createToTable($fileData, $this->sourceFileTable, $this->targetFilePrimaryKey);
	}

	/**
	 * Retrieves input file data for a specific project.
	 * 
	 * @param int $project_id Project ID.
	 * @return Row Input file data.
	 */
	public function getInputFileData(int $project_id): Row
	{
		return $this->db->select('*')
			->from($this->sourceFileTable)
			->where('project_id = %i', $project_id)
			->fetch();
	}

	/**
	 * Updates project settings for a specific project and customer.
	 * 
	 * @param int $project_id Project ID.
	 * @param int $customer_id Customer ID.
	 * @param string $jsonData JSON data for project settings.
	 */
	public function updateProjectSettings(int $project_id, int $customer_id, string $jsonData): void
	{
		$this->db->update($this->getTable(), ['project_settings' => $jsonData])
			->where('project_id = %i', $project_id)
			->where('customer_id = %i', $customer_id)
			->where('visible = 1')
			->execute();
	}

	/**
	 * Updates SOM settings for a specific project and customer.
	 * 
	 * @param int $project_id Project ID.
	 * @param int $customer_id Customer ID.
	 * @param string $jsonData JSON data for SOM settings.
	 */
	public function updateProjectSomSettings(int $project_id, int $customer_id, string $jsonData): void
	{
		$this->db->update($this->getTable(), ['som_settings' => $jsonData])
			->where('project_id = %i', $project_id)
			->where('customer_id = %i', $customer_id)
			->where('visible = 1')
			->execute();
	}

	/**
	 * Submits a project for analysis.
	 * 
	 * @param int $project_id Project ID.
	 * @param int $customer_id Customer ID.
	 * @return int|null|\Dibi\Result Result of the update operation.
	 */
	public function submitProjectToAnalyze(int $project_id, int $customer_id): int|null|\Dibi\Result
	{
		return $this->db->update($this->getTable(), ['ready_to_analyze' => 1])
			->where('project_id = %i', $project_id)
			->where('customer_id = %i', $customer_id)
			->where('visible = 1')
			->execute();
	}


	public function resubmitProjectToAnalyze(int $project_id, int $customer_id): int|null|\Dibi\Result
	{
		return $this->db->update($this->getTable(), ['status' => 0])
			->where('project_id = %i', $project_id)
			->where('customer_id = %i', $customer_id)
			->where('visible = 1')
			->execute();
	}

	public function unlockProjectToAnalyze(int $project_id, int $customer_id): int|null|\Dibi\Result
	{
		return $this->db->update($this->getTable(), ['status' => 0, 'ready_to_analyze' => 0])
			->where('project_id = %i', $project_id)
			->where('customer_id = %i', $customer_id)
			->where('visible = 1')
			->execute();
	}

	/**
	 * Returns appropriate map size based on row count
	 * 
	 * @param int $rowCount Number of rows in the dataset
	 * @return array{0: int, 1: int} Array with map dimensions [m, n]
	 */
	private function getMapSizeByRowCount(int $rowCount): array
	{
		if ($rowCount <= 500) {
			return [10, 10]; // 100 neuronů pro až 500 vzorů (5 vzorů na neuron)
		} elseif ($rowCount <= 2000) {
			return [20, 20]; // 400 neuronů pro až 2000 vzorů (5 vzorů na neuron)
		} else {
			return [30, 30]; // 900 neuronů pro 2000+ vzorů (2+ vzorů na neuron)
		}
	}

	public function getHybridSomSettings(int $project_id): array
	{
		$inputFileData = $this->getInputFileData($project_id);
		$mapSize = $this->getMapSizeByRowCount($inputFileData->row_count);
		
		// Určení epoch_multiplier podle počtu řádků
		if ($inputFileData->row_count <= 500) {
			$epochMultiplier = '10';
		} elseif ($inputFileData->row_count <= 2000) {
			$epochMultiplier = '5';
		} elseif ($inputFileData->row_count <= 5000) {
			$epochMultiplier = '2';
		} else {
			$epochMultiplier = '0.5';
		}

		return [
			'processing_type' => 'hybrid',
			'learning_rate' => 0.9,
			'min_learning_rate' => 0.1,
			'min_radius' => 1,
			'lr_decay_type' => 'linear-drop',
			'radius_decay_type' => 'linear-drop',
			'growth_g' => 15,
			'epoch_multiplier' => $epochMultiplier,
			'map_type' => 'hex',
			'num_batches' => 10,
			'max_batch_percent' => 5,
			'min_batch_percent' => 0.2,
			'batch_growth_type' => 'exp-growth',
			'm' => $mapSize[0],
			'n' => $mapSize[1]
		];
	}

}
