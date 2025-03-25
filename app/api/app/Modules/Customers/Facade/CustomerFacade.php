<?php

declare(strict_types=1);

namespace Api\Modules\Customers\Facade;

use Api\Common\Facade\BaseFacade;
use Api\Modules\Customers\Entity\Customer;
use Api\Modules\Customers\Repository\CustomerRepository;

class CustomerFacade extends BaseFacade
{
    private Customer $customerEntity;
    private CustomerRepository $customerRepository;

    public function __construct(CustomerEntity $customerEntity, CustomerRepository $customerRepository)
    {
        $this->customerEntity = $customerEntity;
        $this->customerRepository = $customerRepository;
    }
}
