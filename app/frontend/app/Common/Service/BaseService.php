<?php

declare(strict_types=1);

namespace App\Common\Service;

use function _PHPStan_f2f2ddf44\Symfony\Component\String\u;

abstract class BaseService
{

    public function getUid(bool $moreEntropy = true): string
    {
        return uniqid('nxmpp', $moreEntropy);
    }
}
