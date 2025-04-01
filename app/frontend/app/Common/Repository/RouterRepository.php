<?php

declare(strict_types=1);

namespace App\Common\Repository;

use Dibi\Row;

/**
 * Repository for managing router configuration and routes
 */
class RouterRepository extends BaseRepository
{
	/** @var string Table name for router configuration */
	protected string $table = 'front_routes';

	/** @var string Primary key column name */
	protected string $primaryKey = 'route_id';

	/** @var array<int,string> Cached modules list */
	private array $modules = [];

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