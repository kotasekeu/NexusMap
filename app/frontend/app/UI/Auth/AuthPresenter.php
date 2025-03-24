<?php

declare(strict_types = 1);

namespace App\Modules\UI;


class AuthPresenter extends BasePresenter
{
	public function __construct()
	{
		
	}

	public function renderDefault()
	{
	}

	public function renderLogin()
	{
		if ($this->getUser()->isLoggedIn()) {
			$this->redirect('Default:default');
		}        
	}

}