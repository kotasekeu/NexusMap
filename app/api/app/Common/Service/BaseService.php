<?php

declare(strict_types=1);

namespace Api\Common\Service;

use Api\Common\Exception\UnauthorizedException;
use Api\Common\Service\AuthServiceTrait;

abstract class BaseService
{
	// use AuthServiceTrait;
	protected int $loggedUserId;	

	
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
		$this->map($row, $entity);

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
}
