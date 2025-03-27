<?php

declare(strict_types=1);

namespace Api\Common\Presenter\Trait;

use Api\Common\Exception\UnauthorizedException;

trait CrudTrait
{
    /**
     * @OpenApi("
     *   summary: Get list of all records
     * ")
     * @Path("")
     * @Method("GET")
     * @Response(200, "List of records")
     * @Response(401, "Unauthorized")
     */
    public function actionDefault(): void
    {
        try {
            $items = $this->facade->findAll();
            $this->sendJson($items);
        } catch (UnauthorizedException $e) {
            $this->sendError($e->getMessage(), 401);
        }
        $this->terminate();
    }

    /**
     * @OpenApi("
     *   summary: Get record by ID
     * ")
     * @Path("/{id}")
     * @Method("GET")
     * @Response(200, "Record detail")
     * @Response(404, "Record not found")
     */
    public function actionDetail(int $id): void
    {       
        $item = $this->facade->findById($id);
        if (!$item) {
            $this->sendError('Record not found', 404);
        }

        $this->sendJson($item);
        $this->terminate();
    }

	/**
	 * @OpenApi("
	 *   summary: Create new record
	 * ")
	 * @Path("")
	 * @Method("POST")
	 * @Response(201, "Record created")
	 * @Response(400, "Invalid input")
	 */
	public function actionCreate(): void
	{
		try {
			$data = $this->getRequestBody(); // změnit na ziskani dat z POST requestu #TODO
			$item = $this->getFacade()->create($data);
			$this->sendJson($item->toArray(), 201);
		} catch (\Exception $e) {
			$this->sendError($e->getMessage(), 400);
		}
		$this->terminate();
	}
} 
