<?php

declare(strict_types=1);

namespace App\Common\Service;

/**
 * Base service class providing common functionality for services.
 */
abstract class BaseService
{
    /**
     * Customer ID.
     * @var int|null
     */
    private ?int $customer_id;

    /**
     * Customer type.
     * @var string|null
     */
    private ?string $customer_type;

    /**
     * Generates a unique identifier.
     * 
     * This method generates a unique identifier based on the current time in microseconds.
     * 
     * @param bool $moreEntropy Whether to add more entropy to the unique identifier.
     * @return string The generated unique identifier.
     */
    public function getUid(bool $moreEntropy = true): string
    {
        return uniqid('nxmpp', $moreEntropy);
    }

    /**
     * Gets the customer ID.
     * 
     * Returns the customer ID set for this service.
     * 
     * @return int The customer ID.
     */
    public function getCustomerId(): int
    {
        return $this->customer_id;
    }

    /**
     * Sets the customer ID.
     * 
     * Sets the customer ID for this service.
     * 
     * @param int $customer_id The customer ID to set.
     */
    public function setCustomerId(int $customer_id): void
    {
        $this->customer_id = $customer_id;
    }

    /**
     * Gets the customer type.
     * 
     * Returns the customer type set for this service.
     * 
     * @return string The customer type.
     */
    public function getCustomerType(): string
    {
        return $this->customer_type;
    }

    /**
     * Sets the customer type.
     * 
     * Sets the customer type for this service.
     * 
     * @param string $customer_type The customer type to set.
     */
    public function setCustomerType(string $customer_type): void
    {
        $this->customer_type = $customer_type;
    }

    /**
     * Begins a transaction.
     * 
     * Starts a transaction on the given repository.
     * 
     * @param object $repository The repository on which to start the transaction.
     */
    public function transactionBegin(object $repository): void
    {
        $repository->transactionBegin();
    }

    /**
     * Commits a transaction.
     * 
     * Commits the transaction on the given repository.
     * 
     * @param object $repository The repository on which to commit the transaction.
     */
    public function transactionCommit(object $repository): void
    {
        $repository->transactionCommit();
    }

    /**
     * Rolls back a transaction.
     * 
     * Rolls back the transaction on the given repository.
     * 
     * @param object $repository The repository on which to roll back the transaction.
     */
    public function transactionRollback(object $repository): void
    {
        $repository->transactionRollback();
    }
}
