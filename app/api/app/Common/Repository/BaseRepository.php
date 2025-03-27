<?php

declare(strict_types=1);

namespace Api\Common\Repository;

use Dibi\Connection;
use Dibi\Row;
abstract class BaseRepository
{
	protected Connection		$db;
	protected string			$table;
	protected string			$primaryKey;

	public function __construct(Connection $connection)
	{
		$this->db = $connection;
	}

	/**
	 * Find all active records
	 * @return array
	 */
	public function findAll(): array
	{
		return $this->db->select('*')
			->from($this->table)
			->where('visible = 1')
			->fetchAll();
	}

	/**
	 * Find record by ID
	 * @param int $id
	 * @return array|null
	 */
	public function findById(int $id): ?Row
	{
		return $this->db->select('*')
			->from($this->table)
			->where('%n = %i AND visible = 1', $this->primaryKey, $id)
			->fetch();
	}

	/**
	 * Create new record
	 * @param array $data
	 * @return int Inserted ID
	 */
	public function create(array $data): int
	{
		$this->db->insert($this->table, $data)
			->execute();
		return $data[$this->primaryKey];
	}

	/**
	 * Delete record (soft delete)
	 * @param int $id
	 * @return bool
	 */
	public function delete(int $id): bool
	{
		return $this->db->update($this->table, ['visible' => 0])
			->where('%n = %i AND visible = 1', $this->primaryKey, $id)
			->execute();
	}
}
