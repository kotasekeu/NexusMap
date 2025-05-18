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


}
