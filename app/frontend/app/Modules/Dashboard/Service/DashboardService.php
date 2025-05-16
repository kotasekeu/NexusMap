<?php

declare(strict_types=1);

namespace App\Modules\Dashboard\Service;

use App\Common\Service\BaseService;

/**
 * Service for handling dashboard data operations
 * 
 * @package App\Modules\Dashboard\Service
 */
class DashboardService extends BaseService
{
	/**
	 * Fetches user data from the API
	 * 
	 * @return ?array User data or null if request fails
	 * 
	 * TODO: Remove debug code (dump and die)
	 * TODO: Implement proper error handling
	 * TODO: Add caching for frequently accessed data
	 * TODO: Consider moving API calls to a separate service
	 */
	public function fetchUsers(): ?array
	{
		// TODO: Remove debug code
		dump('d');
		die;
		
		if (!$this->token) {
			$this->login();
		}

		return $this->fetchData('users');
	}

	/**
	 * Fetches data from the specified API endpoint
	 * 
	 * @param string $endpoint API endpoint to fetch data from
	 * @return ?array Response data or null if request fails
	 * 
	 * TODO: Add request timeout configuration
	 * TODO: Add retry mechanism for failed requests
	 * TODO: Add request logging
	 * TODO: Consider implementing rate limiting
	 */
	private function fetchData(string $endpoint): ?array
	{
		try {
			$response = $this->guzzle->get("{$this->apiBaseUrl}/{$endpoint}", [
				'headers' => [
					'Authorization' => "Bearer {$this->token}",
					'Accept' => 'application/json'
				]
			]);

			return Json::decode($response->getBody()->getContents(), Json::FORCE_ARRAY);
		} catch (RequestException $e) {
			// TODO: Implement proper error handling
			return null;
		}
	}
}
