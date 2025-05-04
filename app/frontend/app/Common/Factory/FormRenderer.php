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

class FormRenderer extends DefaultFormRenderer
{
	/** @var Controls\Button */
	public $primaryButton = null;

	/** @var bool */
	private $controlsInit = false;


	public function __construct()
	{
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

	public function renderBegin(): string
	{
		$this->controlsInit();
		return parent::renderBegin();
	}

	public function renderEnd(): string
	{
		$this->controlsInit();
		return parent::renderEnd();
	}

	public function renderBody(): string
	{
		$this->controlsInit();
		return parent::renderBody();
	}

	public function renderControls($parent): string
	{
		$this->controlsInit();
		return parent::renderControls($parent);
	}

	public function renderPair(Control $control): string
	{
		$this->controlsInit();
		return parent::renderPair($control);
	}

	public function renderPairMulti(array $controls): string
	{
		$this->controlsInit();
		return parent::renderPairMulti($controls);
	}

	public function renderLabel(Control $control): Html
	{
		$this->controlsInit();
		return parent::renderLabel($control);
	}

	public function renderControl(Control $control): Html
	{
		$this->controlsInit();
		return parent::renderControl($control);
	}

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
