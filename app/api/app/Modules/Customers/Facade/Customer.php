<?php

declare(strict_types = 1);

namespace Api\Modules\Customers\Facade;

use Api\Common\Facade\BaseFacade;
use Api\Modules\Customers\Entity\Customer as CustomerEntity;
use Api\Modules\Customers\Model\Customer as CustomerModel;

class Customer extends BaseFacade
{
	/** @var CustomerEntity */
	private $entity;
	private $model;

	public function __construct(CustomerEntity $entity, CustomerModel $model)
	{
		$this->entity = $entity;
		$this->model = $model;
	}

	public function getRowId(): int
	{
		return $this->entity->getRowId();
	}

	public function findById(): int
	{
		return $this->model($this->getId());
	}

	public function getName(): string
	{
		return $this->entity->getName();
	}

	public function getCompany(): ?string
	{
		return $this->entity->getCompany();
	}

	public function getMonthlyTokens(): int
	{
		return $this->entity->getMonthlyTokens();
	}

	public function getRemainingTokens(): int
	{
		return $this->entity->getRemainingTokens();
	}

	public function isVisible(): bool
	{
		return $this->entity->isVisible();
	}

	public function setName(string $name): void
	{
		$this->entity->setName($name);
	}

	public function setCompany(?string $company): void
	{
		$this->entity->setCompany($company);
	}

	public function setMonthlyTokens(int $tokens): void
	{
		$this->entity->setMonthlyTokens($tokens);
	}

	public function setRemainingTokens(int $tokens): void
	{
		$this->entity->setRemainingTokens($tokens);
	}

	public function setVisible(bool $visible): void
	{
		$this->entity->setVisible($visible);
	}
}
