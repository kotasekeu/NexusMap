<?php

declare(strict_types=1);

namespace Api\Modules\Projects\Facade;

use Api\Common\Facade\BaseFacade;
use Api\Common\Facade\Trait\BaseFacadeCrudTrait;
use Api\Modules\Projects\Service\ProjectService;

class ProjectsFacade extends BaseFacade
{
	use BaseFacadeCrudTrait;

	public ProjectService $service;

	public function __construct(ProjectService $service)
	{
		$this->service = $service;
	}

}
