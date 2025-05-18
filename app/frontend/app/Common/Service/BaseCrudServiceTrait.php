<?php

declare(strict_types=1);

namespace App\Common\Service;

use App\Common\Repository\BaseRepository;
use Dibi\Result;
use Dibi\Row;
use Nette\Utils\ArrayHash;

/**
 * Trait BaseCrudServiceTrait provides basic CRUD operations with transaction support and hiding of previous records.
 */
trait BaseCrudServiceTrait
{
    /**
     * Saves a record to the database with transaction support and hides previous records.
     * 
     * This method prepares the data for saving, starts a transaction, hides previous records if necessary, 
     * creates a new record, and commits the transaction. If an error occurs during saving, it rolls back the transaction.
     * 
     * @param array|ArrayHash $data The data to be saved.
     * @param BaseRepository $repository The repository for database operations.
     * @param callable $prepareDataCallback A callback to prepare the data before saving.
     * @return int The ID of the saved record.
     * @throws \Exception If an error occurs during saving.
     */
    protected function saveWithTransaction(
        array|ArrayHash $data,
        BaseRepository $repository,
        callable $prepareDataCallback
    ): int {
        $preparedData = $prepareDataCallback($data);
        
        try {
            $this->transactionBegin($repository);
            
            // Hides previous records
            if (isset($preparedData[$repository->getPrimaryKey()])) {
                $repository->hidePreviousRecords($preparedData[$repository->getPrimaryKey()]);
            }

            // Creates a new record
            $id = $repository->create($preparedData);
            $this->transactionCommit($repository);
            
            return $id;
        } catch (\Exception $e) {
            $this->transactionRollback($repository);
            throw $e;
        }
    }

    /**
     * Deletes a record from the database.
     * 
     * This method hides previous records by setting their visibility to 0.
     * 
     * @param BaseRepository $repository The repository for database operations.
     * @param int $id The ID of the record to be deleted.
     * @return Result|int|null The result of the delete operation.
     */
    public function delete(BaseRepository $repository, int $id): Result|int|null
    {
        return $repository->hidePreviousRecords($id);
    }
} 