<?php

/*

 */

namespace Entities;

use Exception;
use Traversable;

/**
 * Description of default entity
 *
 * @author tomas
 */

class Entity
{
    use \Nette\SmartObject;

	public function __construct(array $detail = null)
	{
		if (! empty($detail)) {
			$this->fill($detail);
		}
	}

	public function fill(array $detail)
	{
		foreach ($detail as $k => $v) {
			$this->$k = $v;
		}
	}

	public function toArray(): array
	{
		return (array) $this;
	}

}
