<?php

namespace Btk;

use App\Model\AclModel;
use App\Model\SettingsModel;
use App\Model\UsersModel;
use Nette;
use Nette\Security\SimpleIdentity;

class RsAuthenticator implements Nette\Security\Authenticator
{
	public $SettingsModel;
	public $UsersModel;
	public $AclModel;
	private $passwords;

	public function __construct(
		SettingsModel 				$SettingsModel,
		UsersModel 					$UsersModel,
		AclModel 					$AclModel,
		Nette\Security\Passwords 	$passwords
	)
    {
        $this->SettingsModel    	= $SettingsModel;
        $this->UsersModel       	= $UsersModel;
        $this->AclModel         	= $AclModel;
		$this->passwords 			= $passwords;
	}

	public function authenticate(string $username, string $password): SimpleIdentity
	{
		$row = $this->UsersModel->getUsersForLogin($username);
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
