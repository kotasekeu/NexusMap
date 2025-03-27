<?php

declare(strict_types=1);

namespace Api\Modules\Customers\Service;

use Api\Common\Service\BaseService;
use Api\Modules\Customers\Entity\Customer;
use Api\Modules\Customers\Repository\CustomerRepository;
use Api\Common\Service\BaseCrudServiceTrait;

class CustomerService extends BaseService
{
	use BaseCrudServiceTrait;

	private CustomerRepository $repository;

	public function __construct(
		CustomerRepository $repository
	) {
		$this->repository = $repository;
	}

	/**
	 * Validate and prepare data before saving
	 */
	public function validateAndPrepareData(array $data): array
	{
		if (isset($data['email'])) {
			$this->validateEmail($data['email']);
			$data['email'] = strtolower($data['email']);
		}
		
		if (isset($data['password'])) {
			$this->validatePassword($data['password']);
			$data['password'] = password_hash($data['password'], PASSWORD_DEFAULT);
		}

		return $data;
	}

	private function validateEmail(string $email): void
	{
		if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
			throw new \InvalidArgumentException('Invalid email format');
		}
	}

	private function validatePassword(string $password): void
	{
		if (strlen($password) < 8) {
			throw new \InvalidArgumentException('Password must be at least 8 characters long');
		}
	}
}
