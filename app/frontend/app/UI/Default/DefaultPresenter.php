<?php

declare(strict_types = 1);

namespace App\Modules\UI;

use App\Models\ApiClient;

class DefaultPresenter extends BasePresenter
{
	private ApiClient $apiClient;

	public function __construct(ApiClient $apiClient)
	{
		$this->apiClient = $apiClient;
	}

	public function renderDefault()
    {
		$q = $this->apiClient->fetchUsers();

		dump($q);

		die("File:" . __FILE__ . "; Line:" . __LINE__);
    }

}