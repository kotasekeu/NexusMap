<?php

declare(strict_types=1);

namespace Api\Modules\Customers\Entity;

use Api\Common\Entity\BaseEntity;

class Customer extends BaseEntity
{
    /** @var int */
    private int $rowId;

    /** @var int */
    private int $customerId;

    /** @var string */
    private string $name;

    /** @var string|null */
    private ?string $company;

    /** @var int */
    private int $monthlyTokens;

    /** @var int */
    private int $remainingTokens;

    /** @var bool */
    private bool $visible;
}
