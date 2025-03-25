<?php

declare(strict_types = 1);

namespace _smazat\Presenters;


use Nette\Application\UI\Presenter;
use Nette\Http\Request;
use Nette\Security\User;

/**
* @Path("/api")
*/
class AuthPresenter extends Presenter
{
	private User $user;
	private Request $httpRequest;

	public function __construct(User $user, Request $httpRequest)
	{
		parent::__construct();
		$this->user = $user;
		$this->httpRequest = $httpRequest;
	}

	/**
	* @Path("/login")
	* @Method("POST")
	* @OpenApi("
	*   summary: Login and get API token.
	* ")
	* @RequestBody({
	*   type: object,
	*   properties: {
	*     username: { type: string, example: 'tomas' },
	*     password: { type: string, example: 'vokurka' }
	*   }
	* })
	*/
	public function actionLogin(): void
	{
//		$data = $this->httpRequest->getPost();
		$data = [
			'username' => 'tomas',
			'password' => 'vokurka',
		];

//		if (!isset($data['username'], $data['password'])) {
//			$this->error('Invalid request', \Nette\Http\IResponse::S400_BadRequest);
//		}

		try {
			$this->user->login($data['username'], $data['password']);
			$token = base64_encode(json_encode(['username' => $data['username'], 'exp' => time() + 3600])); // Platnost 1 hodina
			$this->sendJson(['token' => $token]);
		} catch (\Nette\Security\AuthenticationException $e) {
			$this->error('Invalid credentials', \Nette\Http\IResponse::S401_Unauthorized);
		}
		$this->terminate();
	}
}