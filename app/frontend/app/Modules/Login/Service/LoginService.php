<?php

declare(strict_types=1);

namespace App\Modules\Login\Service;

use App\Common\Service\BaseService;
use App\Modules\Login\Repository\LoginRepository;
use Dibi\Row;

/**
 * Service for handling user authentication and customer information
 * 
 * @package App\Modules\Login\Service
 */
class LoginService extends BaseService
{
	/** @var LoginRepository Repository for accessing customer data */
	private $loginRepository;

	/**
	 * Constructor for LoginService
	 * 
	 * @param LoginRepository $loginRepository Repository for accessing customer data
	 */
	public function __construct(
		LoginRepository					$loginRepository)
	{
		$this->loginRepository			= $loginRepository;
	}

	/**
	 * Retrieves a customer by email
	 * 
	 * @param string $email Customer email
	 * @return ?Row Customer data or null if not found
	 * 
	 * TODO: Consider adding caching for frequently accessed customers
	 * TODO: Consider adding rate limiting for failed login attempts
	 */
	public function getCustomerByEmail(string $email): ?Row
	{
		return $this->loginRepository->getCustomerByEmail($email);
	}
}
