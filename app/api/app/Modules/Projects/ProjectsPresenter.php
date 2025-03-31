<?php

declare(strict_types=1);

namespace Api\Modules\Projects;

use Api\Common\Presenter\BasePresenter;
use Api\Common\Presenter\Trait\CrudPresenterTrait;
use Api\Modules\Projects\Facade\ProjectsFacade;

class ProjectsPresenter extends BasePresenter
{
	use CrudPresenterTrait;

	private ProjectsFacade $facade;

	public function __construct(ProjectsFacade $facade)
	{
		$this->facade = $facade;
	}
}
