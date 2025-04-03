<?php

declare(strict_types=1);

namespace App\Modules\Login\Service;

use App\Common\Service\BaseService;
use App\Modules\Login\Repository\LoginRepository;
use Dibi\Row;

/**
 * LoginService class
 * 
 * This class is responsible for authentication and retrieving customer information.
 */
class LoginService extends BaseService
{
	/** @var LoginRepository */
	private $loginRepository;

	/**
	 * Constructor for LoginService class
	 * 
	 * @param LoginRepository $loginRepository Login repository.
	 */
	public function __construct(
		LoginRepository					$loginRepository)
	{
		$this->loginRepository			= $loginRepository;
	}

	/**
	 * Retrieves a customer by email.
	 * 
	 * @param string $email Customer email.
	 * @return ?Row Customer or null if not found.
	 */
	public function getCustomerByEmail(string $email): ?Row
	{
		return $this->loginRepository->getCustomerByEmail($email);
	}
}
