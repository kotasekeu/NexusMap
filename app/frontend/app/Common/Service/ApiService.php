<?php

declare(strict_types=1);

namespace App\Common\Service;

use GuzzleHttp\Client;
use GuzzleHttp\Exception\GuzzleException;
use Contributte;

class ApiService extends BaseService
{
	private string $apiUrl;
	private Client $httpClient;

	public function __construct(string $apiUrl)
	{
		$this->apiUrl = $apiUrl;
		$this->httpClient = new Client([]);
	}

	/**
	 * @throws GuzzleException
	 */
	public function getProjects(array $filters = []): array
	{
		$response = $this->httpClient->post(self::API_URL . '/projects', [
			'json' => [
				'filters' => $filters
			],
			'headers' => [
				'Content-Type' => 'application/json',
				'Accept' => 'application/json'
			]
		]);

		$data = json_decode($response->getBody()->getContents(), true);

		if (json_last_error() !== JSON_ERROR_NONE) {
			throw new \RuntimeException('Invalid JSON response from API');
		}

		return $data ?? [];
	}
}
