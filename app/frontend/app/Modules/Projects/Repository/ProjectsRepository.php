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

	/**
	 * Retrieves all projects for a specific customer.
	 * 
	 * @param int $customer_id Customer ID.
	 * @return array<Row> Array of project rows.
	 */
	public function getProjectsForCustomer(int $customer_id): array
	{
		return $this->db->select('*')
			->from($this->getTable())
			->where('customer_id = %i', $customer_id)
			->where('visible = 1')
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

}
