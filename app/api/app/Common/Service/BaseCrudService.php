<?php

declare(strict_types=1);

namespace Api\Common\Service;

use Dibi\Row;

trait BaseCrudServiceTrait
{
    	/**
	 * Update existing record by hiding previous record and creating new one.
	 * We use delete() to hide the previous record and create() to insert new version
	 * to maintain history of changes. Transaction ensures we don't lose data if create fails.
	 * @param array $data
	 * @return bool
	 */
	public function update(array $data): bool
	{
		$this->validateToken();
		
		$this->repository->getConnection()->begin();
		try {
			$this->repository->delete($data[$this->repository->primaryKey]);
			$this->repository->create($data);
			$this->repository->getConnection()->commit();
			return true;
		} catch (\Exception $e) {
			$this->repository->getConnection()->rollback();
			return false;
		}
	}

	/**
	 * Find all active records
	 * @throws UnauthorizedException
	 * @return array
	 */
	protected function getFilteredList(array $filter): array
	{
		return $this->repository->getFilteredList($filter);
	}

	/**
	 * Find record by ID
	 * @param int $id
	 * @throws UnauthorizedException
	 * @return array|null
	 */
	public function getOneById(int $id): mixed
	{
		//$this->validateToken(); #TODO
		return $this->convertOneRowToEntity($this->repository->getOneById($id), $this->entity);
	}

	/**
	 * Create new record
	 * @param array $data
	 * @throws UnauthorizedException
	 * @return int Inserted ID
	 */
	protected function create(array $data): int
	{
//		$this->validateToken(); #TODO
 		return $this->repository->create($data);
	}

	/**
	 * Delete record (soft delete)
	 * @param int $id
	 * @throws UnauthorizedException
	 * @return bool
	 */
	protected function delete(int $id): bool
	{
//		$this->validateToken(); #TODO
		return $this->repository->delete($id);
	}

	private function validateToken(): void
	{
		// $this->validateToken(); #TODO
		// TODO: implementovat validaci tokenu
	}
}
