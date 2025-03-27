<?php

declare(strict_types=1);

namespace Api\Modules\Customers\Repository;

use Api\Common\Repositories\BaseRepository;
use Dibi\Connection;

class CustomerRepository extends BaseRepository
{
	protected string $table 		= 'customers';
	protected string $primaryKey 	= 'customer_id';

	public function __construct(Connection $connection) 
	{
		parent::__construct($connection);
	}

	/**
	 * Find customer by email
	 * @param string $email
	 * @return array|null
	 */
	public function findByEmail(string $email): ?array
	{
		return $this->db->select('*')
			->from($this->table)
			->where('email = %s AND visible = 1', $email)
			->fetch();
	}

	/**
	 * Update customer tokens
	 * @param int $customerId
	 * @param int $remainingTokens
	 * @return bool
	 */
	public function updateTokens(int $customerId, int $remainingTokens): bool
	{
		return $this->db->update($this->table, ['remaining_tokens' => $remainingTokens])
			->where('customer_id = %i AND visible = 1', $customerId)
			->execute();
	}
}
