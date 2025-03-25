<?php

declare(strict_types = 1);

namespace _smazat\Presenters;

use League\OAuth2\Server\AuthorizationServer;
use Nette\Application\UI\Presenter;

class OAuth2Presenter extends Presenter
{
	private AuthorizationServer $server;

	public function __construct(AuthorizationServer $server)
	{
		parent::__construct();
		$this->server = $server;
	}

	public function actionToken(): void
	{
		try {
			$response = $this->server->respondToAccessTokenRequest(
			\Laminas\Diactoros\ServerRequestFactory::fromGlobals(),
			new \Laminas\Diactoros\Response()
			);

			$this->sendResponse(new \Nette\Application\Responses\JsonResponse(
			json_decode((string) $response->getBody(), true)
			));
		} catch (\Exception $e) {
			$this->error($e->getMessage()); //, \Nette\Http\IResponse::S400_BAD_REQUEST
		}
	}
}