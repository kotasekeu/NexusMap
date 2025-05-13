<?php

declare(strict_types=1);

namespace App\Modules\Projects;

use App\Common\Presenter\BasePresenter;
use App\Modules\Projects\Forms\ProjectFormFactory;
use App\Modules\Projects\Service\ProjectsService;
use Nette\Application\UI\Form;

class ProjectsPresenter extends BasePresenter
{
	private ProjectsService $projectsService;
	private ProjectFormFactory $projectFormFactory;

	private $projectDetail;

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

		$this->getTemplate()->inputFileData = $this->projectsService->getInputFileData($projectDetail->project_id);
	}


	public function renderStatsData(int $project_id): void
	{
		$this->getTemplate()->title = "Statistická data";

		$projectDetail = $this->projectsService->getProjectDetail($this->getUser()->getId(), $project_id);
		if (!$projectDetail) {
			$this->flashMessage('Projekt nenalezen.');
			$this->redirect('Projects:default');
		}

		$this->getTemplate()->projectDetail = $projectDetail;
		$this->getTemplate()->clusters		= $clusters = $this->projectsService->getClustersData($projectDetail->uid_hash);
		$this->getTemplate()->extremes		= $extremes	= $this->projectsService->getExtremesData($projectDetail->uid_hash);
		$this->getTemplate()->records		= $records	= $this->projectsService->getRecordsData($projectDetail->uid_hash, $projectDetail->project_settings->primary_id);
		$this->getTemplate()->clustersWithData		= $this->projectsService->getStatsDataFromSources($clusters, $extremes, $records, $projectDetail);
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
		$this->getTemplate()->items = $clustersData;
//		dump($clustersData);
//		die("File:" . __FILE__ . "; Line:" . __LINE__);

		$this->getTemplate()->size = $size = 10;

		$counts   = [];
		$maxCount = 0;
		for ($y = 0; $y < $size; $y++) {
			for ($x = 0; $x < $size; $x++) {
				$cnt = isset($clustersData[$y.'_'.$x]) && is_array($clustersData[$y.'_'.$x])
					? count($clustersData[$y.'_'.$x])
					: 0;

				$counts[$y.'_'.$x] = $cnt;
				$maxCount       = max($maxCount, $cnt);
			}
		}

		$this->getTemplate()->counts   = $counts;
		$this->getTemplate()->maxCount = $maxCount;
		$this->getTemplate()->colors   = [
			'#f7fbff','#deebf7','#c6dbef','#9ecae1',
			'#6baed6','#4292c6','#2171b5','#08519c','#08306b'
		];

//		$this->getTemplate()->selectedCell = $this->selectedCell;
	}

	public function handleChangeCell(string $cell)
	{
		die("File:" . __FILE__ . "; Line:" . __LINE__);
//		$jsonDir = WWW_DIR . '/userFiles/' . $projectDetail->uid_hash . '/json';
//		$clustersData = json_decode(file_get_contents($jsonDir . '/clusters.json'), true);
//		ksort($clustersData);
//		$this->selectedCell = $clustersData[$cell];
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

	public function handleSubmit(int $project_id)
	{
		$projectDetail = $this->projectsService->getProjectDetail($this->getUser()->getId(), $project_id);
		if (!$projectDetail) {
			$this->flashMessage('Projekt nenalezen.', 'success');
			$this->redirect('Projects:default');
		}
		$this->projectsService->submitProject($this->getUser()->getId(), $projectDetail);

		$this->flashMessage('Projekt byl odeslán na analýzu.', 'success');
		$this->redirect('Projects:default');
	}

	public function actionEdit(int $project_id): void
	{
		$this->projectDetail = $this->projectsService->getProjectDetail($this->getUser()->getId(), $project_id);
		if (!$this->projectDetail) {
			$this->flashMessage('Projekt nenalezen.');
			$this->redirect('Projects:default');
		}

		$this->getComponent('editProjectForm')->setDefaults(
			array_merge(
				[
					'project_id'	=> $this->projectDetail->project_id,
					'name'			=> $this->projectDetail->name,
				],
				(array)$this->projectDetail->project_settings
			));
	}

	public function actionEditSom(int $project_id): void
	{
		$this->projectDetail = $this->projectsService->getProjectDetail($this->getUser()->getId(), $project_id);
		if (!$this->projectDetail) {
			$this->flashMessage('Projekt nenalezen.');
			$this->redirect('Projects:default');
		}
		if ($this->projectDetail->status == 1 || $this->projectDetail->ready_to_analyze == 1) {
			$this->flashMessage('Projekt který je hotový či probíhá analýza nelze upravovat.');
			$this->redirect('Projects:default');
		}

		$this->getComponent('editSomProjectForm')->setDefaults(
			array_merge(
				[
					'project_id'	=> $this->projectDetail->project_id,
					'name'			=> $this->projectDetail->name,
				],
				(array)$this->projectDetail->som_settings
			));
	}

	public function createComponentCreateProjectForm(): Form
	{
		return $this->projectFormFactory->createForm(
			function ($project_id): void {
				$this->flashMessage('Projekt byl úspěšně vytvořen.');
				$this->redirect("Projects:detail", ['project_id' => $project_id]);
			}
		);
	}

	public function createComponentEditSomProjectForm(): Form
	{
		return $this->projectFormFactory->editSomForm(
			function ($project_id): void {
				$this->flashMessage('Projekt byl upraven.');
				$this->redirect("Projects:detail", ['project_id' => $project_id]);
			},
			$this->projectDetail->project_id
		);
	}

	public function createComponentEditProjectForm(): Form
	{
		return $this->projectFormFactory->editForm(
			function ($project_id): void {
				$this->flashMessage('Projekt byl upraven.');
				$this->redirect("Projects:detail", ['project_id' => $project_id]);
			},
			$this->projectDetail->project_id
		);
	}
}
