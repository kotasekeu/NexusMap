<?php

declare(strict_types=1);

namespace App\Modules\Projects;

use App\Common\Presenter\BasePresenter;

class ProjectsPresenter extends BasePresenter
{

	public function __construct()
	{
		parent::__construct();
	}

	public function renderDefault(): void
	{
	}

	public function renderDetail(int $project_id)
	{
//		$this->getTemplate()->projectDetail = $project_detail = $this->projectsModel->getProjectDetail($project_id);
//		$this->getTemplate()->json = json_decode($project_detail->som_settings);
//
//		$this->getTemplate()->customerDetail = $this->customersModel->getCustomerDetail($project_detail->customer_id);
	}
}
