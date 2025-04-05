<?php

declare(strict_types=1);

namespace App\Modules\Projects\Forms;

use App\Common\Factory\FormFactory;
use Nette;
use Nette\Application\UI\Form;

/**
 * ProjectFormFactory class
 *
 * This class is responsible for creating and managing the project form.
 */
final class ProjectFormFactory
{
	use Nette\SmartObject;

	/** @var FormFactory */
	private $factory;

	/**
	 * Constructor for ProjectFormFactory class
	 *
	 * @param FormFactory	$factory	Form factory.
	 */
	public function __construct(FormFactory $factory)
	{
		$this->factory = $factory;
	}

	/**
	 * Creates and configures the project form.
	 *
	 * @return Form The configured project form.
	 */
	public function createForm(callable $onSuccess): Form
	{
		$form = $this->factory->create();
		$form->addProtection('Platnost formuláře vypršela, obnovte stránku.');


		$form->addSubmit('login', 'Přihlásit se');

		$form->onValidate[] = function (Form $form, ArrayHash $values): void {
//			$customer = $this->loginService->getCustomerByEmail($values->email);
//			if ( empty($customer) ) {
//				$form->addError('Tato kombinace e-mailu a hesla je neplatná');
//			}
		};

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