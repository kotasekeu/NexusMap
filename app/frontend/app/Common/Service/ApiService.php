<?php

declare(strict_types=1);

namespace App\Common\Service;

use GuzzleHttp\Client;
use GuzzleHttp\Exception\GuzzleException;
use Contributte;

/**
 * Service for interacting with the API.
 */
class ApiService extends BaseService
{
	/**
	 * URL of the API.
	 * @var string
	 */
	private string $apiUrl;

	/**
	 * HTTP client for making requests.
	 * @var Client
	 */
	private Client $httpClient;

	/**
	 * Constructor.
	 * 
	 * @param string $apiUrl URL of the API.
	 */
	public function __construct(string $apiUrl)
	{
		$this->apiUrl = $apiUrl;
		$this->httpClient = new Client([]);
	}

	/**
	 * Fetches projects from the API based on filters.
	 * 
	 * @param array $filters Optional filters for the projects.
	 * @return array Array of projects.
	 * @throws GuzzleException If there's an error making the request.
	 */
	public function getProjects(array $filters = []): array
	{
		$response = $this->httpClient->post($this->apiUrl . '/projects', [
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
