<?php

namespace App\Common\Services;

use Nette;
use Nette\Security\SimpleIdentity;

class AuthenticateService implements Nette\Security\Authenticator
{
	private $passwords;

	public function __construct(
		Nette\Security\Passwords 	$passwords
	)
	{
		$this->passwords 			= $passwords;
	}

	public function authenticate(string $username, string $password): SimpleIdentity
	{
		$salt = $this->SettingsModel->getAdminSalt();

		if (!$row) {
			throw new Nette\Security\AuthenticationException('User not found.');
		}

		if (!$this->passwords->verify(\Btk\Helpers::saltPassword($password, $username, $salt), $row->pass)) {
			throw new Nette\Security\AuthenticationException('Invalid password.');
		}

		$row->userSettings = json_decode($row->userSettings);
		$roles = $this->AclModel->getRolesForSelect();

		return new SimpleIdentity (
			$row->idUser,
			$roles[$row->idRole],
			$row
		);
	}
}
