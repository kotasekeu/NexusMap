<?php

declare(strict_types=1);

namespace Tests\Frontend\Components;

use Tester\Assert;
use Tester\TestCase;

require __DIR__ . '/../../bootstrap.php';

class ExampleComponentTest extends TestCase
{
    public function testComponentRendering(): void
    {
        // Zde bude test renderování komponenty
        Assert::true(true);
    }

    public function testComponentData(): void
    {
        // Zde bude test dat komponenty
        Assert::true(true);
    }
}

(new ExampleComponentTest())->run(); 