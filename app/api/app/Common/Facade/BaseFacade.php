<?php

declare(strict_types=1);

namespace Api\Common\Facade;

use Api\Common\Exception\UnauthorizedException;

abstract class BaseFacade
{
	protected int $loggedUserId;
	private AuthService $authService;  // service pro práci s JWT tokenem

	public function __construct(AuthService $authService)
	{
		$this->authService = $authService;
	}

	/**
	 * @throws UnauthorizedException
	 */
	protected function validateToken(): void
	{
		$token = $this->authService->getCurrentToken();
		if (!$token || !$this->authService->isTokenValid($token)) {
			throw new UnauthorizedException('Invalid or missing token');
		}
		$this->loggedUserId = $this->authService->getUserIdFromToken($token);
	}

	public function setLoggedUserId(int $loggedUserId)
	{
		$this->loggedUserId = $loggedUserId;
	}

	protected function map($source, $destination)
	{
		$sourceReflection = new \ReflectionObject($source);
		$destinationReflection = new \ReflectionObject($destination);

		foreach ($sourceReflection->getProperties() as $sourceProperty) {
			$sourceProperty->setAccessible(true);
			$name = $sourceProperty->getName();
			if ($destinationReflection->hasProperty($name)) {
				$destinationProperty = $destinationReflection->getProperty($name);
				$destinationProperty->setAccessible(true);
				$destinationProperty->setValue($destination, $sourceProperty->getValue($source));
			}
		}
	}

	protected function processAttributes($row)
	{
		return $row;
	}

	public function convertRowsToEntity(?array $rows, $entityClass): array
	{
		if ($rows == null) {
			return [];
		}
		$returnData = [];
		foreach ($rows as $row) {
			$returnData[] = $this->convertOneRowToEntity($row, $entityClass);
		}

		return $returnData;
	}

	public function convertOneRowToEntity($row, $entityClass)
	{
		$entity = new $entityClass();
		$this->map($this->processAttributes($row), $entity);

		return $entity;
	}

	public static function prepareDataForDbSave($formValues): array
	{
		return $formValues;
	}

	public function toArray($object): array
	{
		$array = [];
		if (is_object($object)) {
			$array = get_object_vars($object);
		}

		if (is_array($object)) {
			return array_map(function ($value) {
				return $this->toArray($value);
			}, $array);
		}

		return $array;
	}

	/**
	 * Všechny public metody facade by měly volat validateToken
	 */
	public function findAll(): array
	{
		$this->validateToken();
		// implementace
	}

	public function findById(int $id): ?object
	{
		$this->validateToken();
		// implementace
	}
}
