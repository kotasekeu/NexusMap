<?php

declare(strict_types=1);

namespace App\Modules\Projects\Repository;

use App\Common\Repository\BaseRepository;

class ProjectRepository extends BaseRepository
{
	protected string $table 		= 'projects';
	protected string $primaryKey 	= 'project_id';

}
