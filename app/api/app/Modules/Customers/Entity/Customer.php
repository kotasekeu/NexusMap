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
     * Unique row identifier
     * @var int
     */
    private int $rowId;

    /**
     * Customer identifier
     * @var int  
     */
    private int $customerId;

    /**
     * Customer's name
     * @var string
     */
    private string $name;

    /**
     * Customer's email address
     * @var string
     */
    private string $email;

    /**
     * Customer's password
     * @var string
     */
    private string $password;

    /**
     * Customer's company name
     * @var string|null
     */
    private ?string $company;

    /**
     * Number of tokens allocated monthly
     * @var int
     */
    private int $monthlyTokens;

    /**
     * Number of tokens remaining
     * @var int
     */
    private int $remainingTokens;

    /**
     * Customer type identifier
     * @var int
     */
    private int $typeId;

    /**
     * Customer type entity
     * @var CustomerType
     */
    private CustomerType $customerType;
}
