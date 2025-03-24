<?php

declare(strict_types = 1);

namespace Api\Models\Facades;

use Api\Entities\Customer;

class CustomerFacade
{
    /** @var Customer */
    private $customer;

    public function __construct(Customer $customer) 
    {
        $this->customer = $customer;
    }

    public function getRowId(): int
    {
        return $this->customer->getRowId();
    }

    public function getCustomerId(): int 
    {
        return $this->customer->getCustomerId();
    }

    public function getName(): string
    {
        return $this->customer->getName();
    }

    public function getCompany(): ?string
    {
        return $this->customer->getCompany();
    }

    public function getMonthlyTokens(): int
    {
        return $this->customer->getMonthlyTokens();
    }

    public function getRemainingTokens(): int
    {
        return $this->customer->getRemainingTokens();
    }

    public function isVisible(): bool
    {
        return $this->customer->isVisible();
    }

    public function setName(string $name): void
    {
        $this->customer->setName($name);
    }

    public function setCompany(?string $company): void
    {
        $this->customer->setCompany($company);
    }

    public function setMonthlyTokens(int $tokens): void
    {
        $this->customer->setMonthlyTokens($tokens);
    }

    public function setRemainingTokens(int $tokens): void
    {
        $this->customer->setRemainingTokens($tokens);
    }

    public function setVisible(bool $visible): void
    {
        $this->customer->setVisible($visible);
    }
}
