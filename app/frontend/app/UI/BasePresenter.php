<?php

declare(strict_types = 1);

namespace App\Modules\UI;

use Nette\Caching\Cache;
use Contributte;

abstract class BasePresenter extends \Nette\Application\UI\Presenter
{
	public $sessionSection;

    protected function startup()
    {

        parent::startup();
    }

    protected function beforeRender()
    {
        if (!$this->getUser()->isLoggedIn() && $this->getName() !== 'Auth') {
            $this->redirect('Auth:login');
        }
    }

}