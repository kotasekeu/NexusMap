<?php

declare(strict_types=1);

namespace App\Common\Factory;

use Nette\Forms\Control;
use Nette\Forms\Controls\Button;
use Nette\Forms\Controls\Checkbox;
use Nette\Forms\Controls\CheckboxList;
use Nette\Forms\Controls\MultiSelectBox;
use Nette\Forms\Controls\RadioList;
use Nette\Forms\Controls\SelectBox;
use Nette\Forms\Controls\TextInput;
use Nette\Forms\Rendering\DefaultFormRenderer;
use Nette\Utils\Html;

/**
 * Custom form renderer for styling and layout adjustments.
 */
class FormRenderer extends DefaultFormRenderer
{
	/** @var Controls\Button */
	public $primaryButton = null;

	/** @var bool */
	private $controlsInit = false;

	/**
	 * Constructor.
	 */
	public function __construct()
	{
		// Customizing the form layout and styling
		$this->wrappers['controls']['container'] = 'form-control';
		$this->wrappers['pair']['container'] = 'div class="row"';
		$this->wrappers['pair']['.error'] = 'has-error';
		$this->wrappers['control']['container'] = 'div class="col mb-3"';
		$this->wrappers['label']['container'] = null;
		$this->wrappers['label']['requiredsuffix'] = ' *';
		$this->wrappers['control']['description'] = 'span class="help-block"';
		$this->wrappers['control']['errorcontainer'] = 'span class="help-block"';
		$this->wrappers['error']['container'] = null;
		$this->wrappers['error']['item'] = 'div class="alert alert-danger"';
	}

	/**
	 * Renders the form beginning.
	 * 
	 * Initializes controls before rendering the form beginning.
	 * 
	 * @return string The rendered form beginning.
	 */
	public function renderBegin(): string
	{
		$this->controlsInit();
		return parent::renderBegin();
	}

	/**
	 * Renders the form ending.
	 * 
	 * Initializes controls before rendering the form ending.
	 * 
	 * @return string The rendered form ending.
	 */
	public function renderEnd(): string
	{
		$this->controlsInit();
		return parent::renderEnd();
	}

	/**
	 * Renders the form body.
	 * 
	 * Initializes controls before rendering the form body.
	 * 
	 * @return string The rendered form body.
	 */
	public function renderBody(): string
	{
		$this->controlsInit();
		return parent::renderBody();
	}

	/**
	 * Renders form controls.
	 * 
	 * Initializes controls before rendering form controls.
	 * 
	 * @param Control $parent The parent control.
	 * @return string The rendered form controls.
	 */
	public function renderControls($parent): string
	{
		$this->controlsInit();
		return parent::renderControls($parent);
	}

	/**
	 * Renders a single form control pair.
	 * 
	 * Initializes controls before rendering a single form control pair.
	 * 
	 * @param Control $control The control to render.
	 * @return string The rendered form control pair.
	 */
	public function renderPair(Control $control): string
	{
		$this->controlsInit();
		return parent::renderPair($control);
	}

	/**
	 * Renders multiple form control pairs.
	 * 
	 * Initializes controls before rendering multiple form control pairs.
	 * 
	 * @param array $controls The controls to render.
	 * @return string The rendered form control pairs.
	 */
	public function renderPairMulti(array $controls): string
	{
		$this->controlsInit();
		return parent::renderPairMulti($controls);
	}

	/**
	 * Renders a form control label.
	 * 
	 * Initializes controls before rendering a form control label.
	 * 
	 * @param Control $control The control to render the label for.
	 * @return Html The rendered form control label.
	 */
	public function renderLabel(Control $control): Html
	{
		$this->controlsInit();
		return parent::renderLabel($control);
	}

	/**
	 * Renders a form control.
	 * 
	 * Initializes controls before rendering a form control.
	 * 
	 * @param Control $control The control to render.
	 * @return Html The rendered form control.
	 */
	public function renderControl(Control $control): Html
	{
		$this->controlsInit();
		return parent::renderControl($control);
	}

	/**
	 * Initializes form controls.
	 * 
	 * This method is called before rendering any part of the form to apply custom styling and layout.
	 */
	private function controlsInit()
	{
		if ($this->controlsInit) {
			return;
		}

		$this->controlsInit = true;
		$this->form->getElementPrototype()->addClass('form theme-form');

		foreach ($this->form->getControls() as $control) {
			if ($control instanceof Button) {
				$markAsPrimary = $control === $this->primaryButton || (!isset($this->primaryButton) && empty($usedPrimary) && $control->parent instanceof Form);
				if ($markAsPrimary) {
					$class = 'btn btn-primary';
					$usedPrimary = true;
				} else {
					$class = 'btn btn-success';
				}
				$control->getControlPrototype()->addClass($class);

			} elseif ($control instanceof TextInput || $control instanceof SelectBox || $control instanceof MultiSelectBox) {
				$control->getControlPrototype()->addClass('form-control');

			} elseif ($control instanceof Checkbox || $control instanceof CheckboxList || $control instanceof RadioList) {
				if ($control->getSeparatorPrototype()->getName() !== null) {
					$control->getSeparatorPrototype()->setName('div')->addClass($control->getControlPrototype()->type);
				} else {
					$control->getItemLabelPrototype()->addClass($control->getControlPrototype()->type . '-inline');
				}
			}
		}
	}
}
