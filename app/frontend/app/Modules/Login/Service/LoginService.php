<?php

declare(strict_types=1);

namespace App\Modules\Projects;

use App\Common\Services\BaseService;
use App\Modules\Login\Repository\LoginRepository;
use Dibi\Row;

class LoginService extends BaseService
{
	private $loginRepository;

	public function __construct(
		LoginRepository					$loginRepository)
	{
		$this->loginRepository			= $loginRepository;
	}

	public function getCustomerByEmail(string $email): ?Row
	{
		return $this->loginRepository->getCustomerByEmail($email);
	}
}
