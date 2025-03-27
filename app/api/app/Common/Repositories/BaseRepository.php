<?php

declare(strict_types=1);

namespace Api\Common\Repositories;

use Dibi\Connection;

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
	public function findById(int $id): ?array
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
	 * Update existing record by hiding previous record and creating new one
	 * @param array $data
	 * @return bool
	 */
	public function update(array $data): bool
	{
		$this->hidePreviousRecord($data[$this->primaryKey]);
		
		return $this->db->insert($this->table, $data)
			->execute();
	}

	/**
	 * Delete record (soft delete)
	 * @param int $id
	 * @return bool
	 */
	public function delete(int $id): bool
	{
		return $this->db->update($this->table, ['visible' => 0])
			->where('%n = %i', $this->primaryKey, $id)
			->execute();
	}

	/**
	 * Hide previous record
	 * @param int $recordId ID of record to hide
	 * @return bool
	 */
	protected function hidePreviousRecord(int $recordId): bool
	{
		return $this->db->update($this->table, ['visible' => 0])
			->where('%n = %i AND visible = 1', $this->primaryKey, $recordId)
			->execute();
	}
}
