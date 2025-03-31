<?php

declare(strict_types=1);

namespace App\Common\Services;

use GuzzleHttp\Client;
use GuzzleHttp\Exception\GuzzleException;
use Nette\Caching\Cache;
use Contributte;

abstract class ApiService extends BaseService
{
	private const API_URL = 'http://api.nexusmap.l/v1'; // #TODO
	private Client $httpClient;

	public function __construct()
	{
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
