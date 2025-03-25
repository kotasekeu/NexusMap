<?php

declare(strict_types = 1);

namespace Api\Modules\Default;

use Api\Common\Presenter\BasePresenter;
use Nette\Application\Responses\JsonResponse;
use Nette\Neon\Neon;

class DefaultPresenter extends BasePresenter
{
	private string $swaggerFile;

	public function __construct(string $swaggerFile)
	{
		$this->swaggerFile = $swaggerFile;
	}

	public function beforeRender()
	{

	}

	public function actionDefault(): void
	{
		$this->getTemplate()->setFile(__DIR__."/Templates/default.latte");
	}

	public function renderDefault()
	{
		$this->getTemplate()->openApiJsonUrl = $this->link('//Default:swagger'); // URL JSON specifikace
	}

	public function actionSwagger()
	{
		if (!is_readable($this->swaggerFile)) {
			$this->error('File not found', \Nette\Http\IResponse::S404_NotFound);
		}

		$neonData = Neon::decode(file_get_contents($this->swaggerFile));

		if (!is_array($neonData)) {
			$this->error('Invalid NEON format', \Nette\Http\IResponse::S500_InternalServerError);
		}

		$this->sendResponse(new JsonResponse($neonData));
	}
}