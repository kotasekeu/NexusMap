<?php

declare(strict_types=1);

namespace App\Modules\Login\Forms;

use App\Common\Factory\FormFactory;
use Nette;
use Nette\Application\UI\Form;
use Nette\Utils\ArrayHash;

final class LoginFormFactory
{
	use Nette\SmartObject;

	/** @var FormFactory */
	private $factory;

	public function __construct(
		FormFactory					$factory)
	{
		$this->factory				= $factory;
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
			if ($this->loginFacade->isDiredocUidUnique($values['diredoc_uid'], intval($values['diredoc_id'])) == false) {
				$form->addError('Tato kombinace e-mailu a hesla je neplatná');
			}
		};

		$form->onSuccess[] = function (Form $form, ArrayHash $values) use ($onSuccess): void {

			$this->formSuccess($values);

			$onSuccess();
		};

		return $form;
	}

	private function formSuccess($values): int
	{
		$diredoc = $this->diredocFacade->parseEntityFromFormData($values);
		$tags = $diredoc->tags;
		$associated_diredoc = $diredoc->associated_diredoc;

		$diredoc_id = $this->diredocFacade->setDiredoc($diredoc);


//		try {
//			$this->getUser()->login($values->username, $values->password);
//
//			$this->restoreRequest($this->backlink);
//			$this->redirect('MyNotify:default');
//		} catch (NS\AuthenticationException $e) {
//			$form->addError($e->getMessage());
//		}



		return $diredoc_id;
	}
}