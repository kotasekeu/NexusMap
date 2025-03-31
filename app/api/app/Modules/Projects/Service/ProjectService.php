<?php

declare(strict_types=1);

namespace Api\Modules\Projects\Service;

use Api\Common\Service\BaseCrudServiceTrait;
use Api\Common\Service\BaseService;
use Api\Modules\Projects\Entity\Project;
use Api\Modules\Projects\Repository\ProjectRepository;

class ProjectService extends BaseService
{
	use BaseCrudServiceTrait;

	private string $entity;
	private ProjectRepository $repository;

	public function __construct(
		ProjectRepository $repository
	) {
		$this->repository = $repository;
		$this->entity = Project::class;
	}
}
