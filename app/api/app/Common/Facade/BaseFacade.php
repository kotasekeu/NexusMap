<?php

declare(strict_types=1);

namespace Api\Common\Facade;

use App\Common\Exception\ValidationException;

/**
 * Base facade class providing common functionality for all facades
 */
abstract class BaseFacade
{
	/**
	 * Create success response with data
	 * @param mixed $data Response data
	 * @return array Response array with success status and data
	 */
	public function createSuccessResponse($data): array
	{
		return [
			'status' => 'success',
			'data' => $this->toArray($data)
		];
	}

	/**
	 * Create error response with message and code
	 * @param string $message Error message
	 * @param int $code Error code
	 * @return array Response array with error status, code and message
	 */
	public function createErrorResponse(string $message, int $code = 400): array
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
	public function createEmptyResponse(): array
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
	public function validateInputData(array $data): void
	{
		// Implementation in specific facades
	}

	/**
	 * Convert data to array
	 * @param mixed $data Data to convert
	 * @return array Converted data
	 */
	public function toArray(mixed $data): array
	{
		return $this->service->toArray($data);
	}

}
