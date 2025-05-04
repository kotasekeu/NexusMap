<?php

declare(strict_types=1);

namespace App\Modules\Projects\Repository;

use App\Common\Repository\BaseRepository;
use Dibi\Connection;
use Dibi\DriverException;
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

	public function getProjectDetail(int $customer_id, int $project_id): ?Row
	{
		return $this->db->select('*')
			->from($this->getTable())
			->where('customer_id = %i', $customer_id)
			->where($this->getPrimaryKey() . ' = %i', $project_id)
			->where('visible = 1')
			->fetch();
	}

	public function saveInputFileData(array $fileData): void
	{
		$this->createToTable($fileData, $this->sourceFileTable, $this->targetFilePrimaryKey);
	}

	public function getInputFileData(int $project_id): Row
	{
		return $this->db->select('*')
			->from($this->sourceFileTable)
			->where('project_id = %i', $project_id)
			->fetch();
	}

	public function updateProjectSettings(int $project_id, int $customer_id, string $jsonData): void
	{
		$this->db->update($this->getTable(), ['project_settings' => $jsonData])
			->where('project_id = %i', $project_id)
			->where('customer_id = %i', $customer_id)
			->where('visible = 1')
			->execute();
	}

	public function updateProjectSomSettings(int $project_id, int $customer_id, string $jsonData): void
	{
		$this->db->update($this->getTable(), ['som_settings' => $jsonData])
			->where('project_id = %i', $project_id)
			->where('customer_id = %i', $customer_id)
			->where('visible = 1')
			->execute();
	}

	public function submitProjectToAnalyze(int $project_id, int $customer_id): int|null|\Dibi\Result
	{
		return $this->db->update($this->getTable(), ['ready_to_analyze' => 1])
			->where('project_id = %i', $project_id)
			->where('customer_id = %i', $customer_id)
			->where('visible = 1')
			->execute();
	}

}
