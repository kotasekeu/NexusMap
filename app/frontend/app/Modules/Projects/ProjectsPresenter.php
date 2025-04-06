<?php

declare(strict_types=1);

namespace App\Modules\Projects;

use App\Common\Presenter\BasePresenter;
use App\Modules\Projects\Forms\ProjectFormFactory;
use App\Modules\Projects\Service\ProjectsService;
use Nette\Application\UI\Form;

class ProjectsPresenter extends BasePresenter
{
	private $projectsService;
	private $projectFormFactory;

	public function __construct(
		ProjectsService				$projectsService,
		ProjectFormFactory			$projectFormFactory
	)
	{
		$this->projectsService		= $projectsService;
		$this->projectFormFactory	= $projectFormFactory;
	}

	public function renderDefault(): void
	{
		$this->getTemplate()->projects = $this->projectsService->getProjects($this->getUser()->getId());
	}

	public function renderDetail(int $project_id)
	{
		$this->getTemplate()->projectDetail = $this->projectsService->getProjectDetail($this->getUser()->getId(), $project_id);
	}

	public function renderCreate()
	{

		$this->getTemplate()->setFile(__DIR__.'/Templates/edit.latte');

//		dump($this->getTemplate()->getFile());
//		die("File:" . __FILE__ . "; Line:" . __LINE__);
	}

	public function createComponentProjectForm(): Form
	{
		return $this->projectFormFactory->createForm(
			function ($project_id): void {
				$this->flashMessage('Projekt byl úspěšně vytvořen.');
				$this->redirect("Projects:detail", ['project_id' => $project_id]);
			}
		);
	}
}
