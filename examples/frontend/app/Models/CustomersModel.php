<?php

declare(strict_types = 1);

namespace App\Model;

use Dibi\Row;

class CustomersModel extends BaseModel
{
    public string $tableName = 'customers';

	public function getCustomerDetail(int $customerId): Row
	{
		return $this->db->select("*")
			->from($this->tableName)
			->where('customer_id = %i', $customerId)
			->where("visible = 1")
			->fetch();
	}
}