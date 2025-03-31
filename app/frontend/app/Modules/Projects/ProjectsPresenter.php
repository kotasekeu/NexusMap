<?php

declare(strict_types=1);

namespace App\Modules\Projects;

use App\Common\Presenter\BasePresenter;
use GuzzleHttp\Exception\GuzzleException;
use App\Services\ProjectsApiClient;

class ProjectsPresenter extends BasePresenter
{
	private ProjectsApiClient $projectsApiClient;

	public function __construct(ProjectsApiClient $projectsApiClient)
	{
		parent::__construct();
		$this->projectsApiClient = $projectsApiClient;
	}

	public function renderDefault(): void
	{
//		try {
			$this->template->projects = $this->projectsApiClient->getProjects([
				'customer_id' => 1
			]);

//		} catch (GuzzleException $e) {
//			$this->flashMessage('Nepodařilo se načíst projekty: ' . $e->getMessage(), 'error');
//			$this->template->projects = [];
//		}
	}

	public function renderDetail(int $project_id)
	{
//		$this->getTemplate()->projectDetail = $project_detail = $this->projectsModel->getProjectDetail($project_id);
//		$this->getTemplate()->json = json_decode($project_detail->som_settings);
//
//		$this->getTemplate()->customerDetail = $this->customersModel->getCustomerDetail($project_detail->customer_id);
	}
}
