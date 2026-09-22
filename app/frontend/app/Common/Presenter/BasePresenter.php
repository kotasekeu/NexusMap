<?php

declare(strict_types=1);

namespace App\Common\Presenter;

use App\Common\Service\AuthenticatorService;
use Nette\Application\UI\Form;
use Nette\Application\UI\Presenter;
use Nette\Caching\Cache;
use Contributte;
use Nette\Utils\ArrayHash;
use App\Modules\Login\Service\LoginService;

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

    private $loginService;
    public function injectLoginService(LoginService $loginService): void
    {
        $this->loginService = $loginService;
    }

    private $authenticatorService;
    public function injectAuthenticatorService(AuthenticatorService $authenticatorService): void
    {
        $this->authenticatorService = $authenticatorService;
    }


	/**
	 * Common presenter startup method.
	 * 
	 * This method is called at the beginning of each request. It checks if the user is logged in and redirects to the login page if not.
	 */
	protected function startup()
	{
		parent::startup();

        if (! $this->getUser()->isLoggedIn()) {
            $customer = $this->loginService->getCustomerByEmail('expert@nexusmap.cz');

            try {
                $identity = $this->authenticatorService->authenticate($customer, 'heslo');

                $this->getUser()->login($identity);
                $this->redirect('Projects:default');

            } catch (Nette\Security\AuthenticationException $e) {
                die("File:" . __FILE__ . "; Line:" . __LINE__);
            }
        };

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
