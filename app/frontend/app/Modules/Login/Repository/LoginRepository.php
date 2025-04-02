<?php

declare(strict_types=1);

namespace App\Modules\Login\Repository;

use App\Common\Repository\BaseRepository;
use Dibi\Row;

class LoginRepository extends BaseRepository
{
	protected string $table 		= 'customers';
	protected string $primaryKey 	= 'customer_id';

	public function getCustomerByEmail(string $email): ?Row
	{
		return $this->db->select("customer_id, email, name, passhash")
			->from($this->table)
			->where('email = %s', $email)
			->where('visible = 1')
			->where('active = 1')
			->fetch();
	}
}
