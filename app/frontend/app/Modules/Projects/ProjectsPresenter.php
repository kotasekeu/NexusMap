<?php

declare(strict_types=1);

namespace App\Modules\Projects;

use App\Common\Presenter\BasePresenter;
use App\Modules\Projects\Service\ProjectsService;
class ProjectsPresenter extends BasePresenter
{
	private $projectsService;

	public function __construct(ProjectsService $projectsService)
	{
		$this->projectsService = $projectsService;
	}

	public function renderDefault(): void
	{
		$this->getTemplate()->projects = $this->projectsService->getProjects($this->getUser()->getId());
	}

	public function renderDetail(int $project_id)
	{
//		$this->getTemplate()->projectDetail = $project_detail = $this->projectsModel->getProjectDetail($project_id);
//		$this->getTemplate()->json = json_decode($project_detail->som_settings);
//
//		$this->getTemplate()->customerDetail = $this->customersModel->getCustomerDetail($project_detail->customer_id);
	}
}
