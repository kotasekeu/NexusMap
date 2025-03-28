<?php

declare(strict_types=1);

namespace Api\Common\Repository;

use Dibi\Connection;

/**
 * Repository for managing router configuration and routes
 */
class RouterRepository extends BaseRepository
{
	/** @var string Table name for router configuration */
	protected string $table = 'api_routes';

	/** @var string Primary key column name */
	protected string $primaryKey = 'idRoute';

	/** @var array<int,string> Cached modules list */
	private array $modules = [];

	/**
	 * RouterRepository constructor
	 */
	public function __construct(Connection $connection)
	{
		parent::__construct($connection);
	}

	/**
	 * Gets all configured routes from database
	 *
	 * @return array<string,array> Array of route configurations indexed by URL
	 */
	public function getAllRoutes(): array
	{
		return $this->db->select("*")
			->from($this->table)
			->orderBy('`order` ASC')
			->fetchAll();
	}
}