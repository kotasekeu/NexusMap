<?php

declare(strict_types=1);

namespace Api\Modules\Projects\Repository;

use Api\Common\Repository\BaseRepository;

class ProjectRepository extends BaseRepository
{
	protected string $table 		= 'projects';
	protected string $primaryKey 	= 'project_id';

}
