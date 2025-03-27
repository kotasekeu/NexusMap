<?php

declare(strict_types=1);

namespace Api\Modules\Customers;

use Api\Common\Presenter\BasePresenter;
use Api\Common\Presenter\Trait\CrudTrait;
use Api\Modules\Customers\Facade\CustomerFacade;

	/**
	 * @Path("/customers")
	 * @Tag("Customers")
	 */
class CustomersPresenter extends BasePresenter
{
	use CrudTrait;

	private CustomerFacade $facade;

	public function __construct(CustomerFacade $facade)
	{
		$this->facade = $facade;
	}

	/**
	 * @OpenApi("
	 *   summary: Find customer by email
	 * ")
	 * @Path("/email/{email}")
	 * @Method("GET")
	 * @Response(200, "Customer detail")
	 * @Response(404, "Customer not found")
	 */
	public function actionFindByEmail(string $email): void
	{
		$this->validateToken();
		
		$customer = $this->facade->findByEmail($email);
		if (!$customer) {
			$this->sendError('Customer not found', 404);
		}

		$this->sendJson($customer->toArray());
		$this->terminate();
	}

	/**
	 * @OpenApi("
	 *   summary: Update customer tokens
	 * ")
	 * @Path("/{id}/tokens")
	 * @Method("PATCH")
	 * @Response(200, "Tokens updated")
	 * @Response(404, "Customer not found")
	 */
	public function actionUpdateTokens(int $id): void
	{
		$this->validateToken();

		$data = $this->getRequestBody();
		if (!isset($data['remaining_tokens'])) {
			$this->sendError('Missing remaining_tokens parameter', 400);
		}

		$customer = $this->facade->updateTokens($id, (int)$data['remaining_tokens']);
		if (!$customer) {
			$this->sendError('Customer not found', 404);
		}

		$this->sendJson($customer->toArray());
		$this->terminate();
	}
}
