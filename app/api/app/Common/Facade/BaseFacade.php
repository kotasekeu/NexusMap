<?php

declare(strict_types=1);

namespace Api\Common\Facade;

use Api\Common\Facade\Trait\BaseFacadeCrudTrait;
use App\Common\Service\BaseCrudService;
use App\Common\Exception\ValidationException;

/**
 * Base facade class providing common functionality for all facades
 */
abstract class BaseFacade
{
	/** @var BaseCrudService Service instance for CRUD operations */
	protected BaseCrudService $baseCrudService;

	use BaseFacadeCrudTrait;

	/**
	 * Create success response with data
	 * @param mixed $data Response data
	 * @return array Response array with success status and data
	 */
	protected function createSuccessResponse($data): array
	{
		return [
			'status' => 'success',
			'data' => $data
		];
	}

	/**
	 * Create error response with message and code
	 * @param string $message Error message
	 * @param int $code Error code
	 * @return array Response array with error status, code and message
	 */
	protected function createErrorResponse(string $message, int $code = 400): array
	{
		return [
			'status' => 'error',
			'error' => [
				'code' => $code,
				'message' => $message
			]
		];
	}

	/**
	 * Create empty success response
	 * @return array Response array with success status and null data
	 */
	protected function createEmptyResponse(): array
	{
		return [
			'status' => 'success',
			'data' => null
		];
	}

	/**
	 * Validate that required fields are present in data array
	 * @param array $data Data to validate
	 * @param array $fields Required field names
	 * @throws ValidationException When required fields are missing
	 */
	protected function validateRequiredFields(array $data, array $fields): void
	{
		$missing = [];
		foreach ($fields as $field) {
			if (!isset($data[$field])) {
				$missing[] = $field;
			}
		}
		
		if (!empty($missing)) {
			throw new ValidationException('Missing required fields: ' . implode(', ', $missing));
		}
	}

	/**
	 * Validate input data - implementation in specific facades
	 * @param array $data Data to validate
	 */
	protected function validateInputData(array $data): void
	{
		// Implementation in specific facades
	}
}
