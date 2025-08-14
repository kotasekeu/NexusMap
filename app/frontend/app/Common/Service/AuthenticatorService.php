<?php

declare(strict_types=1);

namespace App\Common\Service;

use Dibi\Row;
use Nette;
use Nette\Security\Passwords;
use Nette\Security\IIdentity;
use Nette\Security\SimpleIdentity;

/**
 * AuthenticatorService class
 */
final class AuthenticatorService implements Nette\Security\IAuthenticator
{
	use Nette\SmartObject;

	/** @var Passwords */
	private Passwords $password;

	/** @var string */
	private string $passSalt;

	/**
	 * Constructor for AuthenticatorService class
	 * @param string $passSalt
	 * @param Passwords $password
	 */
	public function __construct(
		String				$passSalt,
		 Passwords			$password
	) 
	{
		$this->password = $password;
		$this->passSalt = $passSalt;
	}

	/**
	 * Performs authentication against the database.
	 * Returns IIdentity on success or throws AuthenticationException
	 * @throws Nette\Security\AuthenticationException
	 */
	public function authenticate(Row $customer, string $password, bool $isCombinedPassword = false): IIdentity
	{
		$combinedPassword = $isCombinedPassword ? $password : $this->generatePassword($customer->email, $password);

		if (!$this->password->verify($combinedPassword, $customer->passhash)) {
			throw new Nette\Security\AuthenticationException('Kombinace e-mailu a hesla je neplatná.');
		}		
		
		return new Nette\Security\SimpleIdentity(
			$customer->customer_id,
			$customer->customer_type,
			[
				'email'		=> $customer->email,
				'name'		=> $customer->name,
				'settings'	=> empty($customer->customer_settings) ? null : json_decode($customer->customer_settings)
			]
		);
	}

	/**
	 * Generates a password
	 * @param string $email
	 * @param string $password
	 * @return string
	 */
	public function generatePassword(string $email, string $password): string
	{
		return sha1($this->passSalt) . sha1($email) . sha1($this->passSalt) . sha1($password) . sha1($this->passSalt);
	}
}