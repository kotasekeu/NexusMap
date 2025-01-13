<?php

declare(strict_types = 1);

namespace App\Modules\UI;

use App\Model\CustomersModel;
use App\Model\ProjectsModel;

class CustomersPresenter extends BasePresenter
{
	protected $customersModel;
	protected $projectsModel;
	public function __construct(CustomersModel $customersModel, ProjectsModel $projectsModel)
	{
		$this->customersModel = $customersModel;
		$this->projectsModel = $projectsModel;
	}

	public function renderDefault()
	{
	}

	public function renderDetail(int $customer_id)
	{
		$this->template->customer = $this->customersModel->getCustomerDetail($customer_id);
		$this->template->projects	= $this->projectsModel->getCustomerProjectsList($customer_id);
	}

}