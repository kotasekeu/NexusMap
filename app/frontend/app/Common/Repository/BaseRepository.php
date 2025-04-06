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
 * @property-read string $table Name of the table the repository works with.
 * @property-read string $primaryKey Name of the primary key of the table.
 */
abstract class BaseRepository
{
	/**
	 * Instance of the database connection.
	 * @var Connection
	 */
	protected Connection		$db;
	
	/**
	 * Name of the table the repository works with.
	 * @var string
	 */
	protected string			$table;
	
	/**
	 * Name of the primary key of the table.
	 * @var string
	 */
	protected string			$primaryKey;

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
	 * Find all active records
	 * 
	 * @param array|null $filters Filters for record selection
	 * @return array Array of all active records
	 */
	public function getFilteredList(?array $filters): array
	{
		return $this->db->select('*')
			->from($this->table)
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
			->from($this->table)
			->where('%n = %i AND visible = 1', $this->primaryKey, $id)
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
		$this->db->insert($this->table, $data)
			->execute();
		return $data[$this->primaryKey];
	}

	/**
	 * Delete record (soft delete)
	 * 
	 * @param int $id Record ID
	 * @return mixed Result of delete operation
	 */
	public function delete(int $id): mixed
	{
		return $this->db->update($this->table, ['visible' => 0])
			->where('%n = %i AND visible = 1', $this->primaryKey, $id)
			->execute();
	}

	/**
	 * Get last ID in table
	 * 
	 * @param string $table Table name
	 * @param string $id_column Column name with ID
	 * @return int Last ID in table
	 */
	public function getLastId(string $table, string $id_column): int
	{
		return $this->db->select('MAX('.$id_column.') AS last_id')
			->from($table)
			->fetchSingle();
	}

	/**
	 * Hide previous records
	 * 
	 * @param string $table Table name
	 * @param string $id_column Column name with ID
	 * @param int $value Value to hide records by
	 * @return bool Success of operation
	 */
	public function hidePreviousRecords(string $table, string $id_column,int $value): bool
	{
		try {
			$this->db->update($table, ["visible" => 0])
				->where("%s = %i", $id_column, $value)
				->where("visible = 1")
				->execute();
			return true;
		} catch (\Exception $e) {
			return false;
		}
	}

}
