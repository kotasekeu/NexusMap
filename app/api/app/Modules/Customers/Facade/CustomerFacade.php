<?php

declare(strict_types=1);

namespace Api\Modules\Customers\Facade;

use Api\Common\Facade\BaseFacade;
use Api\Modules\Customers\Entity\Customer;
use Api\Modules\Customers\Service\CustomerService;

class CustomerFacade extends BaseFacade
{
	private CustomerService $service;

	public function __construct(CustomerService $service)
	{
		$this->service = $service;
	}

//	public function findAll(): array
//	{
//		return $this->convertRowsToEntity(
//			$this->service->findAll(),
//			Customer::class
//		);
//	}
//
//	public function findById(int $id): ?Customer
//	{
//		$data = $this->service->findById($id);
//		return $data ? $this->convertOneRowToEntity($data, Customer::class) : null;
//	}

	public function findByEmail(string $email): ?Customer
	{
		$data = $this->service->findByEmail($email);
		return $data ? $this->convertOneRowToEntity($data, Customer::class) : null;
	}

//	public function create(array $data): Customer
//	{
//		$data = $this->service->validateAndPrepareData($data);
//		$id = $this->service->create($data);
//		return $this->findById($id);
//	}
//
//	public function update(int $id, array $data): ?Customer
//	{
//		$data[$this->service->primaryKey] = $id;
//		$data = $this->service->validateAndPrepareData($data);
//
//		$success = $this->service->update($data);
//		return $success ? $this->findById($id) : null;
//	}
//
//	public function updateTokens(int $id, int $tokens): ?Customer
//	{
//		$success = $this->service->updateTokens($id, $tokens);
//		return $success ? $this->findById($id) : null;
//	}
//
//	public function delete(int $id): bool
//	{
//		return $this->service->delete($id);
//	}
}
