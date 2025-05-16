<?php

declare(strict_types=1);

namespace App\Common\Error;

use Nette\Application\BadRequestException;
use Nette\Application\Helpers;
use Nette\Application\Request;
use Nette\Application\Response as AppResponse;
use Nette\Application\Responses\CallbackResponse;
use Nette\Application\Responses\ForwardResponse;
use Nette\Http\IRequest;
use Nette\Http\IResponse;
use Psr\Log\LogLevel;
use Throwable;
use Tracy\Debugger;
use Tracy\ILogger;

/**
 * Base presenter for handling 5xx HTTP error responses.
 * 
 * This presenter is responsible for handling server-side errors (5xx HTTP status codes).
 * It logs the error details and forwards to a custom error template or a default one.
 */
abstract class Error5xxPresenter
{
	/**
	 * Handles the request and returns a response.
	 * 
	 * This method checks if the request contains an exception parameter. If it does, it logs the exception details.
	 * If the exception is a BadRequestException, it forwards the request to the Error4xxPresenter.
	 * Otherwise, it returns a CallbackResponse that renders a custom error template based on the Content-Type header.
	 * 
	 * @param Request $request The request object.
	 * @return ForwardResponse|CallbackResponse The response object.
	 */
	public function run(Request $request): AppResponse
	{
		$e = $request->getParameter('exception');

		if ($e instanceof Throwable) {
			$code = $e->getCode();
			$level = ($code >= 400 && $code <= 499) ? LogLevel::WARNING : LogLevel::ERROR;

			// Log the exception details
			Debugger::log(sprintf(
				'Code %s: %s in %s:%s',
				$code,
				$e->getMessage(),
				$e->getFile(),
					$e->getLine()
			), $level);

			// Log the exception itself
			Debugger::log($e, ILogger::EXCEPTION);
		}

		if ($e instanceof BadRequestException) {
			// Forward to Error4xxPresenter if the exception is a BadRequestException
			[$module, , $sep] = Helpers::splitName($request->getPresenterName());

			return new ForwardResponse($request->setPresenterName($module . $sep . 'Error4xx'));
		}

		// Return a CallbackResponse that renders a custom error template
		return new CallbackResponse(function (IRequest $httpRequest, IResponse $httpResponse): void {
			$header = $httpResponse->getHeader('Content-Type');
			if ($header !== null && preg_match('#^text/html(?:;|$)#', $header) !== false) {
				require __DIR__ . '/templates/500.phtml';
			}
		});
	}
}
