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
	public function __construct(

    )
	{

	}

	/**
	 * Renders the default view - login form
	 * Redirects to dashboard if user is already logged in
	 */
	public function renderDefault()
	{
        $this->redirect('Projects:default');
	}

}
