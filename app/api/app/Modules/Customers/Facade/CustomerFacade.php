<?php

declare(strict_types=1);

namespace Api\Modules\Customers\Facade;

use Api\Common\Facade\BaseFacade;
use Api\Common\Facade\Trait\BaseFacadeCrudTrait;
use Api\Common\Service\BaseCrudServiceTrait;
use Api\Modules\Customers\Entity\Customer;
use Api\Modules\Customers\Service\CustomerService;

class CustomerFacade extends BaseFacade
{
	use BaseFacadeCrudTrait;

	public CustomerService $service;

	public function __construct(CustomerService $service)
	{
		$this->service = $service;
	}

	public function findByEmail(string $email): ?Customer
	{
		$data = $this->service->findByEmail($email);
		return $data;
	}

	public function updateTokens(Customer $customer, int $tokens): ?Customer
	{
		return $customer;
//		$this->service->updateTokens($customerId, $tokens);
		// #TODO - hide, update, create new
	}
}
