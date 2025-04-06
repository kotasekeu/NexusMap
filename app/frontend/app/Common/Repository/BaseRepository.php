<?php

declare(strict_types=1);

namespace App\Common\Repository;

use Dibi\Connection;
use Dibi\Row;
use Nette\Utils\ArrayHash;

/**
 * Basic repository class for working with the database.
 * 
 * This class provides basic methods for reading, creating, and deleting records in the database.
 * 
 * @property-read Connection $db Instance of the database connection.
 */
abstract class BaseRepository
{
	/**
	 * Instance of the database connection.
	 * @var Connection
	 */
	protected Connection $db;

	/**
	 * Name of the table this repository works with.
	 * @var string
	 */
	protected string $table;

	/**
	 * Name of the primary key column.
	 * @var string
	 */
	protected string $primaryKey;

	/**
	 * Initializes the repository with a database connection.
	 * 
	 * @param Connection $connection Instance of the database connection.
	 */
	public function __construct(Connection $connection)
	{
		$this->db = $connection;
	}

	/**
	 * Get the name of the table this repository works with
	 * 
	 * @return string Table name
	 */
	public function getTable(): string
	{
		return $this->table;
	}

	/**
	 * Get the name of the primary key column
	 * 
	 * @return string Primary key column name
	 */
	public function getPrimaryKey(): string
	{
		return $this->primaryKey;
	}

	/**
	 * Find all active records
	 * 
	 * @param array|null $filters Filters for record selection
	 * @return array Array of all active records
	 */
	public function getFilteredList(?array $filters): array
	{
		return $this->db->select('*')
			->from($this->getTable())
			->where('visible = 1')
			->fetchAll();
	}

	/**
	 * Find record by ID
	 * 
	 * @param int $id Record ID
	 * @return Row|null Found record or null if record was not found
	 */
	public function getOneById(int $id): ?Row
	{
		return $this->db->select('*')
			->from($this->getTable())
			->where('%n = %i AND visible = 1', $this->getPrimaryKey(), $id)
			->fetch();
	}

	/**
	 * Create new record
	 * 
	 * @param array|ArrayHash $data Data for creating new record
	 * @return int ID of newly created record
	 */
	public function create(array|ArrayHash $data): int
	{
		$this->db->insert($this->getTable(), $data)
			->execute();
		return $data[$this->getPrimaryKey()];
	}

	/**
	 * Delete record (soft delete)
	 * 
	 * @param int $id Record ID
	 * @return mixed Result of delete operation
	 */
	public function delete(int $id): mixed
	{
		return $this->db->update($this->getTable(), ['visible' => 0])
			->where('%n = %i AND visible = 1', $this->getPrimaryKey(), $id)
			->execute();
	}

	/**
	 * Get last ID in table
	 * 
	 * @return int Last ID in table
	 */
	public function getNewId(): int
	{
		$last_id = $this->db->select('MAX('.$this->getPrimaryKey().') AS last_id')
			->from($this->getTable())
			->fetchSingle();
		return $last_id + 1;
	}

	/**
	 * Hide previous records
	 * 
	 * @param int $value Value to hide records by
	 * @return bool Success of operation
	 */
	public function hidePreviousRecords(int $value): mixed
	{
		return $this->db->update($this->getTable(), ["visible" => 0])
			->where("%sql = %i", $this->getPrimaryKey(), $value)
			->where("visible = 1")
			->execute();
	}

	public function transactionBegin(): void
	{
		$this->db->begin();
	}

	public function transactionCommit(): void
	{
		$this->db->commit();
	}

	public function transactionRollback(): void
	{
		$this->db->rollback();
	}
}
