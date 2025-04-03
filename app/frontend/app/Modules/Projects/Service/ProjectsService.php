<?php

declare(strict_types=1);

namespace App\Modules\Projects\Service;

use App\Common\Service\BaseService;
use App\Modules\Projects\Repository\ProjectsRepository;

class ProjectsService extends BaseService
{
    private $projectsRepository;

    public function __construct(ProjectsRepository $projectsRepository)
    {
        $this->projectsRepository = $projectsRepository;
    }

    public function getProjects(int $customer_id)
    {
        return $this->projectsRepository->getProjects($customer_id);
    }

}
