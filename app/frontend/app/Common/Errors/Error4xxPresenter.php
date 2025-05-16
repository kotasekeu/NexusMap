<?php

declare(strict_types=1);

namespace App\Common\Errors;

use App\Model\Exception\Runtime\InvalidStateException;
use Nette\Application\BadRequestException;
use Nette\Application\Request;
use Nette\Application\UI\ComponentReflection;

/**
 * Base presenter for handling 4xx HTTP error responses
 */
abstract class Error4xxPresenter
{
	/**
	 * Common presenter startup method
	 * Checks if the request is a forward and handles error state
	 * 
	 * TODO: Consider adding logging for error states
	 * TODO: Consider adding custom error handling for specific error codes
	 */
	public function startup(): void
	{
		if ($this->getRequest() !== null && $this->getRequest()->isMethod(Request::FORWARD)) {
			return;
		}

		$this->error();
	}

	/**
	 * Renders the error template based on the exception code
	 * 
	 * @param BadRequestException $exception The exception that triggered the error
	 * 
	 * TODO: Consider adding support for custom error templates per module
	 * TODO: Consider adding error tracking/analytics
	 * TODO: Consider adding support for different template formats (not just latte)
	 */
	public function renderDefault(BadRequestException $exception): void
	{
		$rf1 = new ComponentReflection(static::class);
		$fileName = $rf1->getFileName();

		// Validate if class is not in PHP core
		if ($fileName === false) {
			throw new InvalidStateException('Class is defined in the PHP core or in a PHP extension');
		}

		$dir = dirname($fileName);

		// Load template 403.latte or 404.latte or ... 4xx.latte
		$file = $dir . '/Templates/' . $exception->getCode() . '.latte';
		$this->template->setFile(is_file($file) ? $file : $dir . '/templates/4xx.latte');
	}
}
