<?php

declare(strict_types=1);

namespace Api\Modules\Customers\Entity;

use Api\Common\Entity\BaseEntity;

/**
 * Entity representing customer type
 */
class CustomerType extends BaseEntity
{
	/**
	 * Unique identifier of customer type
	 * @var int
	 */
	private int $typeId;

	/**
	 * Code identifier of customer type
	 * @var string
	 */
	private string $code;
    
	/**
	 * Display label of customer type
	 * @var string
	 */
	private string $label;
}
