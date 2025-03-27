<?php

declare(strict_types=1);

namespace Api\Modules\Customers;

use Api\Common\Presenter\BasePresenter;
use Api\Modules\Customers\Repository\CustomerRepository;

/**
	 * @Path("/customers")
	 * @Tag("Customers")
	 */
class CustomersPresenter extends BasePresenter
{
	private CustomerRepository $customersRepository;

	public function __construct(CustomerRepository $customersRepository)
	{
		$this->customersRepository = $customersRepository;
//		$this->authPresenter = $authPresenter;
	}

	/**
	 * @OpenApi("
	 *   summary: Get list of all customers
	 * ")
	 * @Path("")
	 * @Method("GET")
	 * @Response(200, "List of customers")
	 */
	public function actionDefault(): void
	{
		$this->validateToken();
		$customers = $this->customersRepository->findAll();
		$this->sendJson($customers);
		$this->terminate();
	}

	/**
	 * @OpenApi("
	 *   summary: Get customer by ID
	 * ")
	 * @Path("/{id}")
	 * @Method("GET")
	 * @Response(200, "Customer detail")
	 * @Response(404, "Customer not found")
	 */
	public function actionDetail(int $id): void
	{
		$this->validateToken();
		
		$customer = $this->customersRepository->findById($id);
		if (!$customer) {
			$this->sendError('Customer not found', 404);
		}

		$this->sendJson($customer);
		$this->terminate();
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
		
		$customer = $this->customersRepository->findByEmail($email);
		if (!$customer) {
			$this->sendError('Customer not found', 404);
		}

		$this->sendJson($customer);
		$this->terminate();
	}

	/**
	 * @OpenApi("
	 *   summary: Create new customer
	 * ")
	 * @Path("")
	 * @Method("POST")
	 * @Response(201, "Customer created")
	 * @Response(400, "Invalid input")
	 */
	public function actionCreate(): void
	{
		$this->validateToken();

		$data = $this->getRequestBody();
		try {
			$id = $this->customersRepository->create($data);
			$customer = $this->customersRepository->findById($id);
			$this->sendJson($customer, 201);
		} catch (\Exception $e) {
			$this->sendError($e->getMessage(), 400);
		}
		$this->terminate();
	}

	/**
	 * @OpenApi("
	 *   summary: Update existing customer
	 * ")
	 * @Path("/{id}")
	 * @Method("PUT")
	 * @Response(200, "Customer updated")
	 * @Response(404, "Customer not found")
	 * @Response(400, "Invalid input")
	 */
	public function actionUpdate(int $id): void
	{
		$this->validateToken();

		$data = $this->getRequestBody();
		$data[$this->customersRepository->primaryKey] = $id;
		
		try {
			$success = $this->customersRepository->update($data);
			if (!$success) {
				$this->sendError('Customer not found', 404);
			}
			$customer = $this->customersRepository->findById($id);
			$this->sendJson($customer);
		} catch (\Exception $e) {
			$this->sendError($e->getMessage(), 400);
		}
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

		$success = $this->customersRepository->updateTokens($id, (int)$data['remaining_tokens']);
		if (!$success) {
			$this->sendError('Customer not found', 404);
		}

		$customer = $this->customersRepository->findById($id);
		$this->sendJson($customer);
		$this->terminate();
	}

	/**
	 * @OpenApi("
	 *   summary: Delete customer
	 * ")
	 * @Path("/{id}")
	 * @Method("DELETE")
	 * @Response(204, "Customer deleted")
	 * @Response(404, "Customer not found")
	 */
	public function actionDelete(int $id): void
	{
		$this->validateToken();

		$success = $this->customersRepository->delete($id);
		if (!$success) {
			$this->sendError('Customer not found', 404);
		}

		$this->sendResponse(new \Nette\Application\Responses\JsonResponse(null, 204));
		$this->terminate();
	}

	private function validateToken(): void
	{		
		// if (!$this->authPresenter->validateToken()) {
		// 	$this->sendError('Invalid or missing token', 401);
		// }
	}
}
