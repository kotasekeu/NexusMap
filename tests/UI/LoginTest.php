<?php

declare(strict_types=1);

use Nette\Application\UI\Form;
use Tester\Assert;
use Tester\TestCase;

require __DIR__ . '/../bootstrap.php';

class LoginTest extends TestCase
{
    private $container;
    private $presenter;

    public function setUp(): void
    {
        $this->container = \App\Bootstrap::bootForTests()->createContainer();
        $this->presenter = $this->container->getByType(\App\Modules\Login\LoginPresenter::class);
    }

    public function testLoginFormCreation()
    {
        $form = $this->presenter->createComponentLoginForm();
        Assert::type(Form::class, $form);
        
        // Test existence polí ve formuláři
        Assert::true($form->hasComponent('username'));
        Assert::true($form->hasComponent('password'));
        Assert::true($form->hasComponent('submit'));
    }

    public function testLoginSuccess()
    {
        $form = $this->presenter->createComponentLoginForm();
        
        // Simulace odeslání formuláře s platnými údaji
        $form->setValues([
            'username' => 'test@example.com',
            'password' => 'password123'
        ]);
        
        $form->onSuccess($form);
        
        // Kontrola, zda je uživatel přihlášen
        Assert::true($this->presenter->getUser()->isLoggedIn());
    }

    public function testLoginFailure()
    {
        $form = $this->presenter->createComponentLoginForm();
        
        // Simulace odeslání formuláře s neplatnými údaji
        $form->setValues([
            'username' => 'invalid@example.com',
            'password' => 'wrongpassword'
        ]);
        
        $form->onSuccess($form);
        
        // Kontrola, zda uživatel není přihlášen
        Assert::false($this->presenter->getUser()->isLoggedIn());
    }

    public function testLogout()
    {
        // Nejprve přihlásíme uživatele
        $this->presenter->getUser()->login('test@example.com');
        Assert::true($this->presenter->getUser()->isLoggedIn());
        
        // Odhlášení
        $this->presenter->actionLogout();
        
        // Kontrola, zda je uživatel odhlášen
        Assert::false($this->presenter->getUser()->isLoggedIn());
    }

    public function testAuthenticator()
    {
        $authenticator = $this->container->getByType(\App\Common\Security\Authenticator::class);
        
        // Test autentizace s platnými údaji
        $identity = $authenticator->authenticate([
            'username' => 'test@example.com',
            'password' => 'password123'
        ]);
        
        Assert::notNull($identity);
        Assert::equal('test@example.com', $identity->getId());
        
        // Test autentizace s neplatnými údaji
        Assert::exception(
            function () use ($authenticator) {
                $authenticator->authenticate([
                    'username' => 'invalid@example.com',
                    'password' => 'wrongpassword'
                ]);
            },
            \Nette\Security\AuthenticationException::class
        );
    }
}

$test = new LoginTest();
$test->run(); 