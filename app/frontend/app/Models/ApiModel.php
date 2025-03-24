<?php

declare(strict_types = 1);

namespace App\Models;

use GuzzleHttp\Client;
use Nette\Http\Request;
use Nette\Utils\Json;

class ApiClient
{
	private string $apiBaseUrl;
	private string $username;
	private string $password;
	private Request $httpRequest;
	private ?string $token = null;

	private $guzzle;

	public function __construct() //Request $httpRequest, string $apiBaseUrl, string $username, string $password
	{
//		$this->httpRequest = $httpRequest;
//		$this->apiBaseUrl = $apiBaseUrl;
//		$this->username = $username;
//		$this->password = $password;

	}

//	public static function fromConfig(Request $httpRequest, array $config): ApiClient
//	{
//		return new self(
//			$httpRequest,
//			$config['apiBaseUrl'],
//			$config['username'],
//			$config['password']
//		);
//	}

	public function login()
	{
		$this->guzzle = new Client([
			'base_uri' => 'http://api.nexusmap.l/v1/',
			'timeout'  => 5.0,
		]);

		try {
			$response = $this->guzzle->get('login');

		} catch (\Exception $e) {
			dump($e->getMessage());
			die("File:" . __FILE__ . "; Line:" . __LINE__);
		}

		try {
			$response = $this->guzzle->get('users');
		} catch (\Exception $e) {
			dump($e->getMessage());
			die("File:" . __FILE__ . "; Line:" . __LINE__);
		}

//		dump(json_decode($response->getBody()->getContents(), true));
//		die("File:" . __FILE__ . "; Line:" . __LINE__);


//		die("File:" . __FILE__ . "; Line:" . __LINE__);
//		$this->guzzle
		$response = $this->guzzle->get($this->apiBaseUrl."/users");

//		dump($response->getBody());
//		die("File:" . __FILE__ . "; Line:" . __LINE__);


		try {
			$response = $this->guzzle->post("{$this->apiBaseUrl}/login", [
				'json' => ['username' => $this->username, 'password' => $this->password]
			]);

			$data = Json::decode($response->getBody()->getContents(), Json::FORCE_ARRAY);
			$this->token = $data['token'] ?? null;
		} catch (RequestException $e) {
			$this->token = null;
		}
	}

	public function fetchUsers(): ?array
	{
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
