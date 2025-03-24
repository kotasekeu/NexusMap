<?php

declare(strict_types = 1);

namespace App\Modules\Dashboard\Service;

use App\Common\Services\BaseService;

class DashboardService extends BaseService
{
	public function fetchUsers(): ?array
	{
		dump('d');die;
		if (!$this->token) {
			$this->login();
		}

		return $this->fetchData('users');
	}

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
			return null;
		}
	}

}