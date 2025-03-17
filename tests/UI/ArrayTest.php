<?php

declare(strict_types = 1);

use Tester\Assert;

require __DIR__ . '/../vendor.s.logy/autoload.php';  # načtení Composer autoloaderu
Tester\Environment::setup();               # inicializace Nette Tester

$stack = [];
Assert::same(0, count($stack));   # očekáváme, že count() vrátí nulu

$stack[] = 'foo';
Assert::same(1, count($stack));   # očekáváme, že count() vrátí jedničku
Assert::contains('foo', $stack);  # ověříme, že $stack obsahuje položku 'foo'
