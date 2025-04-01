<?php

declare(strict_types=1);

namespace App\Modules\Login;

use App\Common\Presenter\BasePresenter;
use App\Modules\Login\Forms\LoginFormFactory;
use Nette\Forms\Form;

class LoginPresenter extends BasePresenter
{
	private LoginFormFactory $loginFormFactory;
	public function __construct(LoginFormFactory $loginFormFactory)
	{
		$this->loginFormFactory = $loginFormFactory;
	}

	public function renderDefault()
	{
		if ($this->getUser()->isLoggedIn()) {
			$this->redirect('Dashboard:default');
		}
	}

	public function createComponentLoginForm(): Form
	{
		return $this->loginFormFactory->loginForm(
			function (): void {
				$this->redirect('Dashboard:default');
			}
		);
	}
}
