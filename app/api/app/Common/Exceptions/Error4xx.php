<?php

declare(strict_types = 1);

namespace Api\Common\Exceptions;

use Nette\Application\BadRequestException;
use Nette\Application\UI\Presenter;
use Tracy\ILogger;

class Error4xx extends Presenter
{
    /** @var ILogger */
    private $logger;

    public function __construct(ILogger $logger)
    {
        $this->logger = $logger;
    }

    public function startup(): void
    {
        parent::startup();
        if (!$this->getRequest()->isMethod('forward')) {
            $this->error();
        }
    }

    public function renderDefault(BadRequestException $exception): void
    {
        // Log error
        $this->logger->log($exception, ILogger::ERROR);
        
        // Set template variables
        $this->template->errorCode = $exception->getCode();
        $this->template->errorMessage = $exception->getMessage();
        
        // Set response code
        $this->getHttpResponse()->setCode($exception->getCode());
        
        // Render template
        $this->setView('4xx');
    }
}
