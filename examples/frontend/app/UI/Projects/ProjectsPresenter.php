<?php

declare(strict_types = 1);

namespace App\Modules\UI;

use App\Model\CustomersModel;
use App\Model\ProjectsModel;

class ProjectsPresenter extends BasePresenter
{
	protected $projectsModel;
	protected $customersModel;
	public function __construct(ProjectsModel $projectsModel,CustomersModel $customersModel)
	{
		$this->projectsModel = $projectsModel;
		$this->customersModel = $customersModel;
	}

	public function renderDefault()
	{
	}

	public function renderDetail(int $project_id)
	{
		$this->getTemplate()->projectDetail = $project_detail = $this->projectsModel->getProjectDetail($project_id);
		$this->getTemplate()->json 			= json_decode($project_detail->som_settings);

//		$this->getTemplate()->customerDetail = $this->customersModel->getCustomerDetail($project_detail->customer_id);
//		dump($this->getTemplate()->projectDetail);
//		die("File:" . __FILE__ . "; Line:" . __LINE__);

	}

}