<?php

declare(strict_types=1);

namespace App\Modules\Projects\Forms;

use App\Modules\Projects\Service\ProjectsService;
use App\Common\Factory\FormFactory;
use Nette;
use Nette\Application\UI\Form;
use Nette\Utils\ArrayHash;

/**
 * ProjectFormFactory class
 *
 * This class is responsible for creating and managing the project form.
 */
final class ProjectFormFactory
{
	use Nette\SmartObject;

	/** @var FormFactory */
	private $factory;

	private $projectsService;

	/**
	 * Constructor for ProjectFormFactory class
	 *
	 * @param FormFactory	$factory	Form factory.
	 */
	public function __construct(
		FormFactory					$factory,
		ProjectsService				$projectsService
	)
	{
		$this->factory				= $factory;
		$this->projectsService		= $projectsService;
	}

	/**
	 * Creates and configures the project form.
	 *
	 * @return Form The configured project form.
	 */
	public function createForm(callable $onSuccess): Form
	{
		$form = $this->factory->create();

		$form->addProtection('Platnost formuláře vypršela, obnovte stránku.');

		$form->addHidden('project_id');

		$form->addText('name', 'Název projektu')
			->setRequired('Vyplňte název projektu');

		$form->addSubmit('submit', 'Uložit projekt');

		$form->onValidate[] = function (Form $form, ArrayHash $values): void {
			// form validation
		};

		$form->onSuccess[] = function (Form $form, ArrayHash $values) use ($onSuccess): void {

			$project_id = $this->projectsService->saveProject($values);
			$onSuccess($project_id);
		};

		return $form;
	}
}