<?php

declare(strict_types=1);

namespace App\Modules\Projects\Service;

use App\Common\Service\BaseService;
use App\Modules\Projects\Repository\ProjectsRepository;
use Dibi\Row;
use Nette\Utils\ArrayHash;

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

	public function saveProject(array|ArrayHash $data): int
	{
		$preparedData = $this->prepareProjectForDb($data);
		return $this->update($preparedData);
	}

	private function prepareProjectForDb(array|ArrayHash $data): array
	{
		return [
			'project_id'	=> intval($data['project_id']) ?: $this->projectsRepository->getNewId(),
			'uid_hash'		=> $this->getUid(),
			'name'			=> $data->name,
			'customer_id'	=> $this->getCustomerId(),
			'som_settings'	=> json_encode([]),
		];
	}

	private function update(array $data): int
	{
		try {
			$this->transactionBegin($this->projectsRepository);
			$this->projectsRepository->hidePreviousRecords($data['project_id']);

			$this->projectsRepository->create($data);
			$this->transactionCommit($this->projectsRepository);
		} catch (\Exception $e) {
			$this->transactionRollback($this->projectsRepository);
			throw $e;
		}

		return $data['project_id'];
	}
}
