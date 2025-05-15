<?php

declare(strict_types=1);

namespace App\Common\Service;


abstract class BaseService
{
	private ?int $customer_id;
	private ?string $customer_type;


    public function getUid(bool $moreEntropy = true): string
    {
        return uniqid('nxmpp', $moreEntropy);
    }

	public function getCustomerId(): int
	{
		return $this->customer_id;
	}

	public function setCustomerId(int $customer_id): void
	{
		$this->customer_id = $customer_id;
	}

	public function getCustomerType(): string
	{
		return $this->customer_type;
	}

	public function setCustomerType(string $customer_type): void
	{
		$this->customer_type = $customer_type;
	}

	public function transactionBegin(object $repository): void
	{
		$repository->transactionBegin();
	}

	public function transactionCommit(object $repository): void
	{
		$repository->transactionCommit();
	}

	public function transactionRollback(object $repository): void
	{
		$repository->transactionRollback();
	}
}
