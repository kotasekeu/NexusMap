<?php

declare(strict_types=1);

namespace App\Common\Factory;

use Nette;
use Nette\Application\UI\Form;

/**
 * Factory for creating forms with a custom renderer.
 */
final class FormFactory
{
	use Nette\SmartObject;

	/**
	 * Creates a new form instance with a custom renderer.
	 * 
	 * This method initializes a new form instance and sets a custom renderer for it.
	 * 
	 * @return Form The newly created form instance.
	 */
	public function create(): Form
	{
		// Initialize a new form instance.
		$form = new Form;
		// Set a custom renderer for the form.
		$form->setRenderer(new FormRenderer());
		// Return the form instance.
		return $form;
	}
}
