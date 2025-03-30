<?php

declare(strict_types=1);

namespace Api\Modules\Customers\Entity;

use Api\Common\Entity\BaseEntity;

/**
 * Entity representing a customer
 */
class Customer extends BaseEntity
{
	/**
	 * Customer identifier
	 * @var int
	 */
	public int $customer_id;

	/**
	 * Customer's name
	 * @var string
	 */
	public string $name;

	/**
	 * Customer's email address
	 * @var string
	 */
	public string $email;

	/**
	 * Customer's password
	 * @var string
	 */
	public string $pass_hash;

	/**
	 * Customer's company name
	 * @var string|null
	 */
	public ?string $company;

	/**
	 * Number of tokens allocated monthly
	 * @var int
	 */
	public int $monthly_tokens;

	/**
	 * Number of tokens remaining
	 * @var int
	 */
	public int $remaining_tokens;
}
