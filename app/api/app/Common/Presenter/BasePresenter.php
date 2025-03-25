<?php

declare(strict_types=1);

namespace Api\Common\Presenter;

use Nette\Application\UI\Presenter;

class BasePresenter extends Presenter
{
    protected function beforeRender()
    {
        parent::beforeRender();
        $this->terminate();
    }
}
