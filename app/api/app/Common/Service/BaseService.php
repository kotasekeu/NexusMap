<?php

declare(strict_types=1);

namespace Api\Common\Service;

use Api\Common\Exception\UnauthorizedException;
use Api\Common\Service\AuthServiceTrait;

abstract class BaseService
{
	// use AuthServiceTrait;
	protected int $loggedUserId;	

	/**
	 * Get repository instance
	 * @return BaseRepository
	 */
	protected function getRepository(): BaseRepository
	{
		return $this->repository;
	}

	/**
	 * Validate and prepare data before saving
	 * This method should be overridden in child classes if needed
	 * @param array $data
	 * @return array
	 */
	protected function validateAndPrepareData(array $data): array
	{
		return $data;
	}
}
