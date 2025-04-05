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
		$this->getTemplate()->projectDetail = $this->projectsService->getProjectDetail($this->getUser()->getId(), $project_id);

	}
}
