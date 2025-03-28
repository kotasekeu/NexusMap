<?php

declare(strict_types=1);

namespace Api\Common\Service;

use Api\Common\Repository\RouterRepository;
use Dibi\Row;	

/**
 * Repository for managing router configuration and routes
 */
class RouterService extends BaseService
{
	/** @var array<int,string> Cached modules list */
	private array $modules = [];

	/** @var RouterRepository */
	private RouterRepository $routerRepository;

	/**
	 * RouterService constructor
	 */
	public function __construct(RouterRepository $routerRepository)
	{
		$this->routerRepository = $routerRepository;
	}

	/**
	 * Gets all configured routes from database
	 *
	 * @return array<string,array> Array of route configurations indexed by URL
	 */
	public function getAllRoutes(): array
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