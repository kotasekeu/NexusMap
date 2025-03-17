<?php

declare(strict_types = 1);

namespace App\Modules\UI;

use Nette\Caching\Cache;
use Contributte;


abstract class BasePresenter extends \Nette\Application\UI\Presenter
{

    /** @inject @var  \Nette\Caching\Storage */
    public $storage;

	public $sessionSection;

    public $cache;

//    public $settings = [];
//
//    /** @inject @var \App\Model\SettingsModel */
//    public $SettingsModel;
//
//    /** @inject @var \Nette\Security\User */
//    public $user;

    protected function startup()
    {
        parent::startup();

		$this->cache = new Cache($this->storage, 'nexusMap');

		$this->sessionSection = $this->getSession('nexusMap');

//        $this->loadSettings();
    }

    protected function beforeRender()
    {
//        $this->template->currentPage        = $this->presenter->name;
    }

//    public function loadSettings()
//    {
//        $cachedData = $this->cache->load('settings_'.$this->locale);
//        if (! empty($cachedData) && Debugger::isEnabled() !== true) {
//			$settings = $cachedData;
//        } else {
//			$settings = $this->SettingsModel->getMainData($this->locale);
//
//            $this->cache->save('settings_'.$this->locale, $settings, [
//                'expire' => time() + 3600 * 24,
//            ]);
//        }
//
//        $this->settings 					= $settings;
//
//		$this->template->settings 			= $this->settings;
//		$this->template->projectVersion     = Debugger::isEnabled() === true ? time() : $this->settings->projectVersion;
//    }
}