<?php

declare(strict_types=1);

namespace App\Modules\Login;

use App\Common\Presenter\BasePresenter;

class LoginPresenter extends BasePresenter
{
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
