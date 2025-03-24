<?php

declare(strict_types = 1);

namespace App\Modules;

use Nette;
use App\Common\Presenter\BasePresenter;
use App\Modules\Dashboard\Service\DashboardService;

class DashboardPresenter extends BasePresenter
{
	private DashboardService $dashboardService;

	public function __construct(DashboardService $dashboardService)
	{
		$this->dashboardService = $dashboardService;
	}

	public function renderDefault()
    {
		// $q = $this->dashboardService->fetchUsers();

		// dump($q);

		// die("File:" . __FILE__ . "; Line:" . __LINE__);
    }

}