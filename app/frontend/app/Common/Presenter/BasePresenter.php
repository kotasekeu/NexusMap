<?php

declare(strict_types=1);

namespace App\Common\Presenter;

use Nette\Application\UI\Presenter;
use Nette\Caching\Cache;
use Contributte;

/**
 * Base presenter for all presenters in the application.
 * 
 * This presenter provides common functionality for all presenters, such as user authentication checks and template setup.
 */
abstract class BasePresenter extends Presenter
{
	/**
	 * Session section for storing presenter-specific data.
	 * 
	 * This property is used to store data specific to the presenter in the session.
	 * 
	 * @var mixed
	 */
	public $sessionSection;

	/**
	 * Common presenter startup method.
	 * 
	 * This method is called at the beginning of each request. It checks if the user is logged in and redirects to the login page if not.
	 */
	protected function startup()
	{
		parent::startup();

		if (!$this->getUser()->isLoggedIn() && !($this->getPresenter()->getName() == 'Modules:Login'
			&& in_array($this->getPresenter()->getAction(), ['default', 'autologin']))) {
			$this->redirect('Login:default');
		}
	}

	/**
	 * Method called before the presenter is rendered.
	 * 
	 * This method sets up the template for the presenter. It sets the template file based on the current action and passes user data to the template if the user is logged in.
	 */
	protected function beforeRender()
	{
		$presenterReflection = new \ReflectionClass($this);
		$presenterDir = dirname($presenterReflection->getFileName());
		$this->getTemplate()->setFile($presenterDir . "/Templates/{$this->getAction()}.latte");
		if ($this->getUser()->isLoggedIn()) {
			$this->getTemplate()->userId = $this->getUser()->getIdentity()->getId();
			$this->getTemplate()->userData  = $this->getUser()->getIdentity()->getData();
		}
	}

	/**
	 * Sets a custom template for the presenter.
	 * 
	 * This method sets a custom template file for the presenter based on the provided template name.
	 * 
	 * @param string $template The name of the template to set.
	 */
	protected function setTemplate(string $template)
	{
		$presenterReflection = new \ReflectionClass($this);
			$presenterDir = dirname($presenterReflection->getFileName());
		$this->getTemplate()->setFile($presenterDir . "/Templates/{$template}.latte");
	}
}
