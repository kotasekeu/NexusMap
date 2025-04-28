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

	public function startup()
	{
		parent::startup();
		$this->projectsService->setCustomerId($this->getUser()->getId());
	}

	public function renderDefault(): void
	{
		$this->getTemplate()->projects = $this->projectsService->getProjects($this->getUser()->getId());
	}

	public function renderDetail(int $project_id)
	{
		$projectDetail = $this->projectsService->getProjectDetail($this->getUser()->getId(), $project_id);
		if (!$projectDetail) {
			$this->flashMessage('Projekt nenalezen.');
			$this->redirect('Projects:default');
		}

		$this->getTemplate()->projectDetail = $projectDetail;

		$this->getTemplate()->projectFiles = $this->projectsService->getProjectFiles($this->getUser()->getId(), $projectDetail->uid_hash);
		$this->getTemplate()->projectVisualizations = $this->projectsService->getProjectFiles($this->getUser()->getId(), $projectDetail->uid_hash, "visualization");

		$this->getTemplate()->somConfig = $this->projectsService->getProjectConfig($projectDetail);
		$this->getTemplate()->somConfigDescription = $this->projectsService->getConfigDescription();
		$this->getTemplate()->projectConfigDescription = $this->projectsService->getProjectConfigDescription();
	}

	public function renderCreate()
	{
		$this->getTemplate()->setFile(__DIR__.'/Templates/edit.latte');
	}

	public function renderMap(int $project_id)
	{
		$projectDetail = $this->projectsService->getProjectDetail($this->getUser()->getId(), $project_id);
		if (!$projectDetail) {
			$this->flashMessage('Projekt nenalezen.');
			$this->redirect('Projects:default');
		}

		$this->getTemplate()->projectDetail = $projectDetail;
		$somConfig = $this->projectsService->getProjectConfig($projectDetail);
		$this->getTemplate()->somConfig = $somConfig;

		$jsonDir = WWW_DIR . '/userFiles/' . $projectDetail->uid_hash . '/json';

		// $extremesData = json_decode(file_get_contents($jsonDir . '/extremes.json'), true);		
		// $this->getTemplate()->extremesData = $extremesData;
		// dump($extremesData);

		$clustersData = json_decode(file_get_contents($jsonDir . '/clusters.json'), true);		
		ksort($clustersData);
		$this->getTemplate()->clustersData = $clustersData;		
	}

	public function handleDelete(int $project_id)
	{
		$projectDetail = $this->projectsService->getProjectDetail($this->getUser()->getId(), $project_id);
		if (!$projectDetail) {
			$this->flashMessage('Projekt nenalezen.', 'success');
			$this->redirect('Projects:default');
		}
		$this->projectsService->deleteProject($this->getUser()->getId(), $projectDetail);

		$this->flashMessage('Projekt byl smazán.', 'success');
		$this->redirect('Projects:default');
	}

	public function actionEdit(int $project_id)
	{
		$projectDetail = $this->projectsService->getProjectDetail($this->getUser()->getId(), $project_id);
		if (!$projectDetail) {
			$this->flashMessage('Projekt nenalezen.');
			$this->redirect('Projects:default');
		}
		$this->getComponent('projectForm')->setDefaults($projectDetail);
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
