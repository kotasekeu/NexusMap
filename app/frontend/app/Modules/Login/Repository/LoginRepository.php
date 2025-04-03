<?php

declare(strict_types=1);

namespace App\Modules\Login\Repository;

use App\Common\Repository\BaseRepository;
use Dibi\Row;

/**
 * LoginRepository class
 * 
 * This class extends BaseRepository and provides methods for managing customer login.
 */
class LoginRepository extends BaseRepository
{
	protected string $table 		= 'customers';
	protected string $primaryKey 	= 'customer_id';

	/**
	 * Retrieves a customer by email.
	 * 
	 * @param string $email Customer email.
	 * @return ?Row Customer or null if not found.
	 */
	public function getCustomerByEmail(string $email): ?Row
	{
		return $this->db->select("customer_id, email, name, passhash,customer_settings")
			->from($this->table)
			->where('email = %s', $email)
			->where('visible = 1')
			->where('active = 1')
			->fetch();
	}
}
