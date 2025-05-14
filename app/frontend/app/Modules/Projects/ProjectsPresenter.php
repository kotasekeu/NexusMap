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

		$this->getTemplate()->visualizationTypes = [
			'hit'        => 'Mapa návštěvnosti',
			'u-matrix'   => 'U-Matrix',
			'pie-map'    => 'Koláčová mapa',
			'component'  => 'Mapa atributů',
			'distance'   => 'Mapa kvantizační chyby',
			'cluster'    => 'Mapa klastrů',
			'mqe-history'=> 'Vývoj kvantizační chyby v čase'
		];

		$this->getTemplate()->visualizationTypesDescription = [
			'hit'        => 'Ukazuje počet vzorků namapovaných na každý neuron.',
			'u-matrix'   => 'Zobrazuje vzdálenosti mezi sousedními neurony pro identifikaci hranic.',
			'pie-map'    => 'Pro každou buňku vykresluje koláčový graf složení kategorií ve vzorcích.',
			'component'  => 'Heatmapa hodnot jednotlivých vstupních atributů v každém neuronu.',
			'distance'   => 'Průměrná kvantizační chyba (vzdálenost vzorku od BMU) pro každý neuron.',
			'cluster'    => 'Zobrazení přiřazení původních vzorků ke klastrům (neurony).',
			'mqe-history'=> 'Graf zobrazuje vývoj kvantizační chyby v čase. '
		];
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

	public function renderMap(int $project_id, string $map_name): void
	{
		$projectDetail = $this->projectsService->getProjectDetail($this->getUser()->getId(), $project_id);
		if (!$projectDetail) {
			$this->flashMessage('Projekt nenalezen.');
			$this->redirect('Projects:default');
		}

		if ($projectDetail->som_settings->map_type == "hex") {
			$this->setTemplate("map_hex");
		} else {
			$this->setTemplate("map_square");
		}

		$this->getTemplate()->projectDetail 	= $projectDetail;
		$this->getTemplate()->clusters			= $clusters = $this->projectsService->getClustersData($projectDetail->uid_hash);
		$this->getTemplate()->extremes			= $extremes	= $this->projectsService->getExtremesData($projectDetail->uid_hash);
		$this->getTemplate()->records			= $records	= $this->projectsService->getRecordsData($projectDetail->uid_hash, $projectDetail->project_settings->primary_id);
		$this->getTemplate()->clustersWithData	= $this->projectsService->getStatsDataFromSourcesForMap($clusters, $extremes, $records, $projectDetail);

		$this->getTemplate()->projectDetail = $projectDetail;
		$this->getTemplate()->mapName	= $map_name;
	}

	public function renderMapCellDetail(int $project_id, int $cell_x, int $cell_y): void
	{
		die("File:" . __FILE__ . "; Line:" . __LINE__);
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
					'name'			=> $this->projectDetail->name
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
					'map_size'		=> $this->projectDetail->som_settings->m . "x" . $this->projectDetail->som_settings->n
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
