<?php

declare(strict_types=1);

namespace UI;

use App\Security\Authenticator;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;
use GuzzleHttp\Psr7\Response;
use Nette\Security\AuthenticationException;
use PHPUnit\Framework\TestCase;

final class AuthenticatorTest extends TestCase
{
	public function testAuthenticateSuccess(): void
	{
		$httpClient = $this->createMock(Client::class);
		$httpClient->method('post')
			->willReturn(new Response(200, [], json_encode([
				'customer_id' => 1,
				'name' => 'example_user',
				'company' => 'Example Corp',
				'monthly_tokens' => 100,
				'remaining_tokens' => 50,
			])));

		$authenticator = new Authenticator($httpClient);
		$identity = $authenticator->authenticate('example_user', 'example_password');

		$this->assertEquals(1, $identity->getId());
		$this->assertEquals('example_user', $identity->getData()['name']);
		$this->assertEquals('Example Corp', $identity->getData()['company']);
	}

	public function testAuthenticateInvalidPassword(): void
	{
		$httpClient = $this->createMock(Client::class);
		$httpClient->method('post')
			->willThrowException(new ClientException(
				'Invalid credentials.',
				new Response(401, [], json_encode(['detail' => 'Invalid password']))
			));

		$authenticator = new Authenticator($httpClient);

		$this->expectException(AuthenticationException::class);
		$this->expectExceptionMessage('Invalid credentials.');
		$authenticator->authenticate('example_user', 'wrong_password');
	}

	public function testAuthenticateUserNotFound(): void
	{
		$httpClient = $this->createMock(Client::class);
		$httpClient->method('post')
			->willThrowException(new ClientException(
				'User not found or inactive.',
				new Response(401, [], json_encode(['detail' => 'User not found or inactive']))
			));

		$authenticator = new Authenticator($httpClient);

		$this->expectException(AuthenticationException::class);
		$this->expectExceptionMessage('Invalid credentials.');
		$authenticator->authenticate('nonexistent_user', 'example_password');
	}
}
