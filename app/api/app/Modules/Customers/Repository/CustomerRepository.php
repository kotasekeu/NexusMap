<?php

declare(strict_types=1);

namespace Api\Modules\Customers\Repository;

use Api\Common\Repositories\BaseRepository;
use Dibi\Connection;

class CustomerRepository extends BaseRepository
{
	private Connection $db;

	public function __construct(Connection $connection)
	{
		$this->db = $connection;
	}

	public function findAll(): array
	{
		return $this->db->select('*')
			->from('customers')
			->where('visible = 1')
			->fetchAll();
	}

	public function findById(int $id): ?array
	{
		return $this->db->select('*')
			->from('customers')
			->where('id = %i', $id)
			->fetch();
	}

	public function create(array $data): array
	{
		$this->db->insert('customers', $data)
			->execute();
		$id = $this->db->getInsertId();
		return $this->findById($id);
	}

	public function update(int $id, array $data): ?array
	{
		$this->db->update('customers', $data)
			->where('id = %i', $id)
			->execute();
		return $this->findById($id);
	}

	public function delete(int $id): bool
	{
		try {
			$this->db->delete('customers')
				->where('id = %i', $id)
				->execute();
			return true;
		} catch (\Exception $e) {
			return false;
		}
	}

	public function updateTokens(int $id, int $tokens): bool
	{
		try {
			$this->db->update('customers', ['remaining_tokens' => $tokens])
				->where('id = %i', $id)
				->execute();
			return true;
		} catch (\Exception $e) {
			return false;
		}
	}
}
