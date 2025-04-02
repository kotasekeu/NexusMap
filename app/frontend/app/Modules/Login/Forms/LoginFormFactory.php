<?php

declare(strict_types=1);

namespace App\Modules\Login\Forms;

use App\Common\Factory\FormFactory;
use App\Modules\Projects\LoginService;
use Nette;
use Nette\Application\UI\Form;
use Nette\Utils\ArrayHash;

final class LoginFormFactory
{
	use Nette\SmartObject;

	/** @var FormFactory */
	private $factory;

	private $loginService;

	public function __construct(
		FormFactory					$factory,
		LoginService				$loginService)
	{
		$this->factory				= $factory;
		$this->loginService			= $loginService;
	}

	public function loginForm(callable $onSuccess): Form
	{
		$form = $this->factory->create();
		$form->addProtection();

		$form->addEmail('email', 'E-mailová adresa')
			->setRequired('Vyplňte email');

		$form->addPassword('passwd', 'Heslo')
			->setRequired('Vyplňte heslo');

		$form->addSubmit('login', 'Přihlásit se');

		$form->onValidate[] = function (Form $form, ArrayHash $values): void {
			$customer = $this->loginService->getCustomerByEmail($values->email);
			if ( empty($customer) ) {
				$form->addError('Tato kombinace e-mailu a hesla je neplatná');
			}
		};

		$form->onSuccess[] = function (Form $form, ArrayHash $values) use ($onSuccess): void {

			$customer = $this->loginService->getCustomerByEmail($values->email);

			try {
				$this->getUser()->login($values->username, $values->password);

				$this->restoreRequest($this->backlink);
				$this->redirect('MyNotify:default');
			} catch (NS\AuthenticationException $e) {
				$form->addError($e->getMessage());
			}

			$this->formSuccess($values);
			$onSuccess();
		};

		return $form;
	}

	private function formSuccess($values): int
	{
		return $this->getUser()->getId();
	}
}