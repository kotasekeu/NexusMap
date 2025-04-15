<?php

declare(strict_types=1);

namespace App\Common\Service;

use App\Common\Repository\BaseRepository;
use Dibi\Row;
use Nette\Utils\ArrayHash;

trait BaseCrudServiceTrait
{
    /**
     * Uloží záznam do databáze s podporou transakcí a skrýváním předchozích záznamů
     * 
     * @param array|ArrayHash $data Data pro uložení
     * @param BaseRepository $repository Repository pro práci s databází
     * @param callable $prepareDataCallback Callback pro přípravu dat před uložením
     * @return int ID uloženého záznamu
     * @throws \Exception Při chybě při ukládání
     */
    protected function saveWithTransaction(
        array|ArrayHash $data,
        BaseRepository $repository,
        callable $prepareDataCallback
    ): int {
        $preparedData = $prepareDataCallback($data);
        
        try {
            $this->transactionBegin($repository);
            
            // Skryjeme předchozí záznamy
            if (isset($preparedData[$repository->getPrimaryKey()])) {
                $repository->hidePreviousRecords($preparedData[$repository->getPrimaryKey()]);
            }

            // Vytvoříme nový záznam
            $id = $repository->create($preparedData);
            $this->transactionCommit($repository);
            
            return $id;
        } catch (\Exception $e) {
            $this->transactionRollback($repository);
            throw $e;
        }
    }

	public function delete(BaseRepository $repository, int $id): Row|int|null
	{
		return $repository->hidePreviousRecords($id);
	}
} 