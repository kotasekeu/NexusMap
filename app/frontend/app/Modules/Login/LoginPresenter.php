<?php

declare(strict_types=1);

namespace App\Modules\Login;

use App\Common\Presenter\BasePresenter;
use App\Modules\Login\Forms\LoginFormFactory;
use Nette\Forms\Form;

/**
 * LoginPresenter class
 */
class LoginPresenter extends BasePresenter
{
	/** @var LoginFormFactory */
	private LoginFormFactory $loginFormFactory;

	/**
	 * Constructor for LoginPresenter class
	 * @param LoginFormFactory $loginFormFactory
	 */
	public function __construct(LoginFormFactory $loginFormFactory)
	{
		$this->loginFormFactory = $loginFormFactory;
	}

	/**
	 * Renders the default view
	 */
	public function renderDefault()
	{
		if ($this->getUser()->isLoggedIn()) {
			$this->redirect('Dashboard:default');
		}
	}

	/**
	 * Creates and returns the login form component
	 * @return Form
	 */
	public function createComponentLoginForm(): Form
	{
		return $this->loginFormFactory->loginForm(
			function ($identity): void {
				$this->getUser()->login($identity);
				$this->redirect('Dashboard:default');
			}
		);
	}

	public function actionLogout(): void
	{
		$this->getUser()->logout();

		$this->flashMessage('You have been logged out.', 'success');
		$this->redirect('Login:default');

	}
}
