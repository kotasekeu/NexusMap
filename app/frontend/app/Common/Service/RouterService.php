<?php

declare(strict_types=1);

namespace App\Common\Service;

use App\Common\Repository\RouterRepository;
use Dibi\Row;
use Nette\Caching\Cache;
use Nette\Caching\Storage;

/**
 * Repository for managing router configuration and routes
 */
class RouterService extends BaseService
{
	private const CACHE_KEY			= 'router.routes';
	private const CACHE_EXPIRATION	= '1 day';

	/** @var array<int,string> Cached modules list */
	private array $modules = [];

	/** @var RouterRepository */
	private RouterRepository $routerRepository;
	private Cache $cache;

	/**
	 * RouterService constructor
	 */
	public function __construct(
		RouterRepository $routerRepository,
		Storage $storage
	) {
		$this->routerRepository = $routerRepository;
		$this->cache = new Cache($storage);
	}

	/**
	 * Gets all configured routes from database or cache
	 *
	 * @return array<string,array> Array of route configurations indexed by URL
	 */
	public function getAllRoutes(): array
	{
		$routes = $this->cache->load(self::CACHE_KEY);

		if ($routes === null) {
			$routes = $this->loadRoutesFromDatabase();
			$this->cache->save(self::CACHE_KEY, $routes, [
				Cache::EXPIRE => self::CACHE_EXPIRATION
			]);
		}

		return $routes;
	}

	/**
	 * Loads routes from database and formats them
	 *
	 * @return array<string,array>
	 */
	private function loadRoutesFromDatabase(): array
	{
		$data = $this->routerRepository->getAllRoutes();

		if (empty($data)) {
			return [];
		}

		$returnData = [];
		foreach ($data as $item) {
			$returnData[$item->url_pattern] = $this->prepareData($item);
		}

		return $returnData;
	}

	/**
	 * Prepares route data from database row
	 *
	 * @param Row $data Database row with route configuration
	 * @return array Prepared route configuration
	 */
	private function prepareData(Row $data): array
	{
		$urlData = [
			'presenter' => $data->presenter,
			'action' => $data->action
		];

		$parameters = [];
		if (!empty($data->parameters)) {
			$parameters = (array)json_decode($data->parameters);
		}

		return array_merge($urlData, $parameters);
	}
}