<?php

declare(strict_types=1);

namespace Api\Modules\Customers;

use Api\Common\Presenter\BasePresenter;
use Api\Common\Presenter\Trait\CrudPresenterTrait;
use Api\Modules\Customers\Facade\CustomerFacade;

	/**
	 * @Path("/customers")
	 * @Tag("Customers")
	 */
class CustomersPresenter extends BasePresenter
{
	use CrudPresenterTrait;

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
		$customer = $this->facade->findByEmail($email);
		if (!$customer) {
			$this->facade->createErrorResponse('Customer not found', 404);
		}

		$this->sendJson(
			$this->facade->createSuccessResponse($customer)
		);

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
	public function actionUpdateTokens(int $id, int $tokens): void
	{
		$customer = $this->facade->getOneById($id);

		if (!$customer) {
			$this->facade->createErrorResponse('Customer not found', 404);
		}

		$customer = $this->facade->updateTokens($customer, $tokens);

		$this->sendJson(
			$this->facade->createSuccessResponse($customer)
		);

		$this->terminate();
	}
}
