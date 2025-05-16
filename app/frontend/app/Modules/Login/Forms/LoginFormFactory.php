<?php

declare(strict_types=1);

namespace App\Modules\Login\Forms;

use App\Common\Factory\FormFactory;
use App\Common\Service\AuthenticatorService;
use App\Modules\Login\Service\LoginService;
use Nette;
use Nette\Application\UI\Form;
use Nette\Utils\ArrayHash;
use Nette\Security\Passwords;
use App\Common\Service\Authenticator;

/**
 * Factory for creating and managing login forms
 * 
 * @package App\Modules\Login\Forms
 */
final class LoginFormFactory
{
	use Nette\SmartObject;

	/** @var FormFactory Factory for creating forms */
	private $factory;

	/** @var LoginService Service for handling login operations */
	private $loginService;

	/** @var Passwords Utility for password hashing and verification */
	private $passwords;

	/** @var AuthenticatorService Service for user authentication */
	private $authenticatorService;

	/**
	 * Constructor for LoginFormFactory
	 * 
	 * @param FormFactory $factory Factory for creating forms
	 * @param LoginService $loginService Service for handling login operations
	 * @param Passwords $passwords Utility for password hashing and verification
	 * @param AuthenticatorService $authenticatorService Service for user authentication
	 */
	public function __construct(
		FormFactory					$factory,
		LoginService				$loginService,
		Passwords					$passwords,
		AuthenticatorService		$authenticatorService)
	{
		$this->factory				= $factory;
		$this->loginService			= $loginService;
		$this->passwords			= $passwords;
		$this->authenticatorService	= $authenticatorService;
	}

	/**
	 * Creates and configures the login form
	 * 
	 * @param callable $onSuccess Callback function to be executed on form success
	 * @return Form The configured login form
	 */
	public function loginForm(callable $onSuccess): Form
	{
		$form = $this->factory->create();
		$form->addProtection('Platnost formuláře vypršela, obnovte stránku.');

		$form->addEmail('email', 'E-mailová adresa')
			->setRequired('Vyplňte email');

		$form->addPassword('passwd', 'Heslo')
			->setRequired('Vyplňte heslo');

		$form->addSubmit('login', 'Přihlásit se');

		// TODO: Consider moving validation logic to a separate method
		$form->onValidate[] = function (Form $form, ArrayHash $values): void {
			$customer = $this->loginService->getCustomerByEmail($values->email);
			if (empty($customer)) {
				$form->addError('Tato kombinace e-mailu a hesla je neplatná');
			}
		};

		// TODO: Consider moving authentication logic to a separate method
		$form->onSuccess[] = function (Form $form, ArrayHash $values) use ($onSuccess): void {
			$customer = $this->loginService->getCustomerByEmail($values->email);

			try {
				$identity = $this->authenticatorService->authenticate($customer, $values->passwd);
			} catch (Nette\Security\AuthenticationException $e) {
				$form->addError($e->getMessage());
			}

			$onSuccess($identity);
		};

		return $form;
	}
}