<?php

declare(strict_types = 1);

namespace _smazat\Presenters;

use Nette\Application\Responses\JsonResponse;
use Nette\Neon\Neon;

class DefaultPresenter extends BasePresenter
{

	public function beforeRender()
	{

	}

	public function actionDefault(): void
	{
//		die("File:" . __FILE__ . "; Line:" . __LINE__);
	}

	public function renderDefault()
	{
		$this->getTemplate()->openApiJsonUrl = $this->link('//Default:swagger'); // URL JSON specifikace
	}

	public function actionSwagger()
	{
		$filePath = __DIR__ . '/../config/swagger.neon';

		if (!is_readable($filePath)) {
			$this->error('File not found', \Nette\Http\IResponse::S404_NOT_FOUND);
		}

		$neonData = Neon::decode(file_get_contents($filePath));

		if (!is_array($neonData)) {
			$this->error('Invalid NEON format', \Nette\Http\IResponse::S500_INTERNAL_SERVER_ERROR);
		}

		$this->sendResponse(new JsonResponse($neonData));
	}
}