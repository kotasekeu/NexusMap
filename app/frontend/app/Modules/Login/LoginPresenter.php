<?php

declare(strict_types=1);

namespace App\Modules\Login;

use App\Common\Presenter\BasePresenter;
use App\Modules\Login\Forms\LoginFormFactory;
use Nette\Forms\Form;
use App\Common\Service\AuthenticatorService;
use App\Modules\Login\Service\LoginService;

/**
 * Presenter for handling user authentication
 * 
 * @package App\Modules\Login
 */
class LoginPresenter extends BasePresenter
{
	/** @var LoginFormFactory Factory for creating login forms */
	private LoginFormFactory $loginFormFactory;

	/**
	 * Constructor for LoginPresenter
	 * 
	 * @param LoginFormFactory $loginFormFactory Factory for creating login forms
	 */
	public function __construct(
		LoginFormFactory $loginFormFactory
    )
	{
		$this->loginFormFactory	= $loginFormFactory;
	}

	/**
	 * Renders the default view - login form
	 * Redirects to dashboard if user is already logged in
	 */
	public function renderDefault()
	{
		if ($this->getUser()->isLoggedIn()) {
			$this->redirect('Projects:default');
		}
	}

	/**
	 * Creates and returns the login form component
	 * 
	 * @return Form The configured login form
	 */
	public function createComponentLoginForm(): Form
	{
		return $this->loginFormFactory->loginForm(
			function ($identity): void {
				$this->getUser()->login($identity);
				$this->redirect('Projects:default');
			}
		);
	}

	/**
	 * Handles user logout
	 * Logs out the user and redirects to login page
	 */
	public function actionLogout(): void
	{
		$this->getUser()->logout();

		$this->flashMessage('You have been logged out.', 'success');
		$this->redirect('Login:default');
	}
}
