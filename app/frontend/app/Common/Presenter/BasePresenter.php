<?php

declare(strict_types = 1);

namespace App\Common\Presenter;

use Nette\Application\UI\Presenter;
use Nette\Caching\Cache;
use Contributte;

abstract class BasePresenter extends Presenter
{
	public $sessionSection;

    protected function startup()
    {

        parent::startup();
    }

    protected function beforeRender()
    {
        $presenterReflection = new \ReflectionClass($this);
        $presenterDir = dirname($presenterReflection->getFileName());
        $this->template->setFile($presenterDir . "/Templates/{$this->getAction()}.latte");
        
        // if (!$this->getUser()->isLoggedIn() && $this->getName() !== 'Login:login') {
        //     $this->redirect('Login:Login:default');
        // }
    }

}