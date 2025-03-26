<?php

declare(strict_types=1);

namespace Api\Modules\Customers;

use Api\Common\Presenter\BasePresenter;
use Api\Modules\Customers\Repository\Customer;

/**
	 * @Path("/customers")
	 * @Tag("Customers")
	 */
class CustomersPresenter extends BasePresenter
{
	private $customersRepository;

	public function __construct(Customer $customersRepository)
	{
		$this->customersRepository = $customersRepository;
//		$this->authPresenter = $authPresenter;
	}

	/**
	 * @OpenApi("
	 *   summary: Get list of customers.
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
	 *   summary: Get customer detail by IP.
	 * ")
	 * @Path("/detail/{ip}")
	 * @Method("GET")
	 * @Response(200, "Customer detail")
	 * @Response(404, "Customer not found")
	 */
	public function actionDetail(string $ip): void
	{
		$this->validateToken();

		$customer = $this->customersRepository->findByIp($ip);
		if (!$customer) {
			$this->sendError('Customer not found', 404);
		}

		$this->sendJson($customer);
		$this->terminate();
	}

	/**
	 * @OpenApi("
	 *   summary: Create new customer.
	 * ")
	 * @Path("/create")
	 * @Method("POST")
	 * @Response(201, "Customer created")
	 * @Response(400, "Invalid input")
	 */
	public function actionCreate(): void
	{
		$this->validateToken();

		$data = $this->getRequestBody();
		try {
			$customer = $this->customersRepository->create($data);
			$this->sendJson($customer, 201);
		} catch (\Exception $e) {
			$this->sendError($e->getMessage(), 400);
		}
		$this->terminate();
	}

	/**
	 * @OpenApi("
	 *   summary: Update existing customer.
	 * ")
	 * @Path("/update/{id}")
	 * @Method("PUT")
	 * @Response(200, "Customer updated")
	 * @Response(404, "Customer not found")
	 */
	public function actionUpdate(int $id): void
	{
		$this->validateToken();

		$data = $this->getRequestBody();
		try {
			$customer = $this->customersRepository->update($id, $data);
			if (!$customer) {
				$this->sendError('Customer not found', 404);
			}
			$this->sendJson($customer);
		} catch (\Exception $e) {
			$this->sendError($e->getMessage(), 400);
		}
		$this->terminate();
	}

	/**
	 * @OpenApi("
	 *   summary: Delete customer.
	 * ")
	 * @Path("/delete/{id}")
	 * @Method("DELETE")
	 * @Response(204, "Customer deleted")
	 * @Response(404, "Customer not found")
	 */
	public function actionDelete(int $id): void
	{
		$this->validateToken();

		$result = $this->customersRepository->delete($id);
		if (!$result) {
			$this->sendError('Customer not found', 404);
		}

		$this->sendResponse(new \Nette\Application\Responses\JsonResponse(null, 204));
		$this->terminate();
	}

	private function validateToken(): void
	{
		if (!$this->authPresenter->validateToken()) {
			$this->sendError('Invalid or missing token', 401);
		}
	}
}
