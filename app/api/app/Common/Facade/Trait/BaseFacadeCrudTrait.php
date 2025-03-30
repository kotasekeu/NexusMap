<?php

declare(strict_types=1);

namespace Api\Common\Facade\Trait;

/**
 * Base trait for CRUD operations in facades
 */
trait BaseFacadeCrudTrait
{
    /**
     * Get single record by ID
     * @param int $id Record ID
     * @return array Response with found record
     */
	public function getOneById(int $id): array
	{
		return $this->createSuccessResponse(
			$this->baseCrudService->getOneById($id)
		);
	}

    /**
     * Get filtered list of records
     * @param array $filters Optional filters to apply
     * @return array Response with filtered records
     */
	public function getFilteredList(array $filters = []): array
	{
		return $this->createSuccessResponse(
			$this->baseCrudService->getFilteredList($filters)
		);
	}

    /**
     * Create new record
     * @param array $data Record data
     * @return array Response with created record
     */
	public function create(array $data): array
	{
		$this->validateInputData($data);
		return $this->createSuccessResponse(
			$this->baseCrudService->create($data)
		);
	}

    /**
     * Update existing record
     * @param array $data Record data with ID
     * @return array Response with updated record
     */
	public function update(array $data): array
	{
		$this->validateInputData($data);
		return $this->createSuccessResponse(
			$this->baseCrudService->update($data)
		);
	}

    /**
     * Delete record by ID
     * @param int $id Record ID
     * @return array Empty success response
     */
	public function delete(int $id): array
	{
		$this->baseCrudService->delete($id);
		return $this->createEmptyResponse();
	}
}
