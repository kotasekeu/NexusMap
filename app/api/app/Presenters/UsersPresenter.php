<?php

declare(strict_types = 1);

namespace Api\Presenters;

use Nette\Application\UI\Presenter;

	/**
	 * @Path("/users")
	 * @Tag("Users")
	 */
class UsersPresenter extends BasePresenter
{
	/**
	 * @OpenApi("
	 *   summary: Get list of users.
	 * ")
	 * @Path("")
	 * @Method("GET")
	 * @Response(200, "List of users")
	 */
	public function actionDefault(): void
	{
//		if (!$this->user->isLoggedIn()) {
//			$this->error('Unauthorized', \Nette\Http\IResponse::S401_Unauthorized);
//		}
		$users = [
			["id" => 1, "name" => "John Doe"],
			["id" => 2, "name" => "Jane Doe"]
		];

		$this->sendJson($users);
	}

	/**
	 * @OpenApi("
	 *   summary: Get user by email.
	 * ")
	 * @Path("/email")
	 * @Method("GET")
	 * @RequestParameter(name="email", in="query", type="string", description="User e-mail address")
	 * @Response(200, "User found")
	 * @Response(404, "User not found")
	 */
	public function actionByEmail(): void
	{
		$email = $this->getParameter('email');

		$users = [
			"john@example.com" => ["id" => 1, "name" => "John Doe"],
			"jane@example.com" => ["id" => 2, "name" => "Jane Doe"]
		];

		if (isset($users[$email])) {
			$this->sendJson($users[$email]);
		} else {
			$this->error("User not found", \Nette\Http\IResponse::S404_NOT_FOUND);
		}
	}
}