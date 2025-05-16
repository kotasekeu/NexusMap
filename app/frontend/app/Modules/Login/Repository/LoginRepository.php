<?php

declare(strict_types=1);

namespace App\Modules\Login\Repository;

use App\Common\Repository\BaseRepository;
use Dibi\Row;

/**
 * Repository for managing customer login data
 * 
 * @package App\Modules\Login\Repository
 */
class LoginRepository extends BaseRepository
{
	/** @var string Name of the customers table */
	protected string $table 		= 'customers';
	
	/** @var string Primary key column name */
	protected string $primaryKey 	= 'customer_id';

	/**
	 * Retrieves a customer by email
	 * 
	 * @param string $email Customer email
	 * @return ?Row Customer data or null if not found
	 * 
	 * TODO: Consider adding indexes on email, visible and active columns for better performance
	 * TODO: Consider adding logging for failed login attempts
	 * TODO: Consider adding support for case-insensitive email search
	 */
	public function getCustomerByEmail(string $email): ?Row
	{
		return $this->db->select("customer_id, email, name, passhash, customer_settings, customer_type")
			->from($this->table)
			->where('email = %s', $email)
			->where('visible = 1')
			->where('active = 1')
			->fetch();
	}
}
