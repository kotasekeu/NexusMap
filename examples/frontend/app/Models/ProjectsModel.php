<?php

declare(strict_types = 1);

namespace App\Model;

use Dibi\Row;

class ProjectsModel extends BaseModel
{
	public string $tableName = 'projects';

	public function getCustomerProjectsList(int $customerId): array
	{
		return $this->db->select("*")
			->from($this->tableName)
			->where('customer_id = %i', $customerId)
			->where("visible = 1")
			->fetchAll();
	}

	public function getProjectDetail(int $project_id): Row
	{
		return $this->db->select("*")
			->from($this->tableName)
			->where('project_id = %i', $project_id)
			->where("visible = 1")
			->fetch();
	}
}

