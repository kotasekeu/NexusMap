<?php

declare(strict_types = 1);

namespace App\Modules\Customers;

use App\Common\Services\BaseService;

class CustomersPresenter extends BaseService
{
	public function __construct()
	{

	}

	public function renderDefault()
	{
	}

	public function renderDetail(int $customer_id)
	{
//		$this->template->customer = $this->customersModel->getCustomerDetail($customer_id);
//		$this->template->projects	= $this->projectsModel->getCustomerProjectsList($customer_id);
	}

}