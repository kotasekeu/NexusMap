<?php

namespace Api\Security\Repositories;

use League\OAuth2\Server\Entities\ClientEntityInterface;
use League\OAuth2\Server\Entities\ScopeEntityInterface;
use League\OAuth2\Server\Entities\AuthCodeEntityInterface;
use League\OAuth2\Server\Entities\TokenInterface;
use League\OAuth2\Server\Repositories\AccessTokenRepositoryInterface;
use League\OAuth2\Server\Repositories\ClientRepositoryInterface;
use League\OAuth2\Server\Repositories\ScopeRepositoryInterface;
use League\OAuth2\Server\Repositories\AuthCodeRepositoryInterface;


class AccessTokenRepository implements AccessTokenRepositoryInterface
{
	public function persistNewAccessToken(TokenInterface $accessToken)
	{
		// Uložení tokenu
	}

	public function revokeAccessToken($tokenId)
	{
		// Zneplatnění tokenu
	}

	public function isAccessTokenRevoked($tokenId)
	{
		return false; // Kontrola, zda je token neplatný
	}

	public function getNewToken(ClientEntityInterface $clientEntity, array $scopes, $userIdentifier = null)
	{
		// TODO: Implement getNewToken() method.
	}
}

class ClientRepository implements ClientRepositoryInterface
{
	public function getClientEntity($clientIdentifier)
	{
		return new ClientEntity(); // Vrácení entity klienta
	}

	public function validateClient($clientIdentifier, $clientSecret, $grantType)
	{
		return true; // Validace klienta
	}
}

class ScopeRepository implements ScopeRepositoryInterface
{
	public function getScopeEntityByIdentifier($identifier)
	{
		return new ScopeEntity(); // Vrácení entity scope
	}

	public function finalizeScopes(array $scopes, $grantType, ClientEntityInterface $clientEntity, $userIdentifier = null)
	{
		// TODO: Implement finalizeScopes() method.
	}
}

class AuthCodeRepository implements AuthCodeRepositoryInterface
{
	public function persistNewAuthCode(AuthCodeEntityInterface $authCodeEntity)
	{
		// Uložení autorizačního kódu
	}

	public function revokeAuthCode($codeId)
	{
		// Zneplatnění autorizačního kódu
	}

	public function isAuthCodeRevoked($codeId)
	{
		return false; // Kontrola, zda je autorizační kód neplatný
	}

	public function getNewAuthCode()
	{
		// TODO: Implement getNewAuthCode() method.
	}
}
