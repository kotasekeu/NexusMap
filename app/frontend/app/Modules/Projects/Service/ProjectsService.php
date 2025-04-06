<?php

declare(strict_types=1);

namespace App\Modules\Projects\Service;

use App\Common\Service\BaseService;
use App\Modules\Projects\Repository\ProjectsRepository;
use Cassandra\Uuid;
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

	public function createProject(array|ArrayHash $data)
	{
		dump(0);
		die("File:" . __FILE__ . "; Line:" . __LINE__);
		$project_uid = $this->getUid();
//		if (! empty ( $data->project_id)
		dump($data);
		die("File:" . __FILE__ . "; Line:" . __LINE__);
		dump($project_uid);

	}

	private function prepareProjectForDb(array|ArrayHash $data): array
	{

		return [];
	}
	/*
	public function setRisk($values)
	{
		$data = $this->prepareRisk($values);

		$this->hidePreviousRecords($this->table_name, 'risk_id', $data['risk_id']);
		$this->saveDbItem($data);

		if ( empty($data['risk_id']) ) {
			$this->taskModel->addNewTaskFromNewRisk();
			return $this->getLastRiskId();
		}

		return $data['risk_id'];
	}

	public function prepareRisk($values)
	{
		$data = [];

		if(empty($values['risk_id'])){
			$risk_id 		= $this->getLastRiskId()+1;
			$data['trend']	= $this->getTrendForRisk();
		}else{
			$risk_id 		= $values->risk_id;
			$oldRate = $this->getRateByRiskId($values->risk_id);
			if (isset($values->probability) && isset($values->significance)) {
				$data['trend']	= $this->getTrendForRisk(intval($values->probability * $values->significance), $oldRate);
			}
		}

		$data['author_id']          = self::$author_id;

		return $data;
	}
	 */

}
