<?php

declare(strict_types=1);

namespace App\Common\Services;

use Nette\Caching\Cache;
use Contributte;

abstract class ApiService extends BaseService
{
	protected function startup()
	{
		parent::startup();
	}
}
