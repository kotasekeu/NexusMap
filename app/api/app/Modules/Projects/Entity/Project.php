<?php

declare(strict_types=1);

namespace Api\Modules\Projects\Entity;

use Api\Common\Entity\BaseEntity;

class Project extends BaseEntity
{
	/** @var int Project identifier */
	public int $project_id;

	/** @var string Unique hash identifier */
	public string $uid_hash;

	/** @var int Foreign key to customers table */
	public int $customer_id;

	/** @var string Project name */
	public string $name;

	/** @var bool Flag indicating if analysis is completed */
	public bool $analysis_done = false;

	/** @var int|null ID of associated result */
	public ?int $result_id = null;

	/** @var string JSON settings for SOM */
	public string $som_settings;

}
