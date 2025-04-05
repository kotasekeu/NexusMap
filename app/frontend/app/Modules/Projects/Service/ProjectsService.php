<?php

declare(strict_types=1);

namespace App\Modules\Projects\Service;

use App\Common\Service\BaseService;
use App\Modules\Projects\Repository\ProjectsRepository;
use Dibi\Row;

class ProjectsService extends BaseService
{
    private $projectsRepository;

    public function __construct(ProjectsRepository $projectsRepository)
    {
        $this->projectsRepository = $projectsRepository;
    }

    public function getProjects(int $customer_id)
    {
        return $this->projectsRepository->getProjectsForCustomer($customer_id);
    }

	public function getProjectDetail(int $customer_id, int $project_id)
	{
		return $this->prepareProject(
			$this->projectsRepository->getProjectDetail($customer_id, $project_id)
		);

	}

	private function prepareProject(Row $project)
	{
		$project->settings = json_decode($project->som_settings);
		unset($project->som_settings);

		return $project;
	}

}
