<?php

declare(strict_types=1);

namespace App\Api\Security;

use Nette\Http\Request;
use Nette\Security\User;
use Nette\Application\Responses\JsonResponse;

class AuthMiddleware
{
    private Request $httpRequest;
    private User $user;

    public function __construct(Request $httpRequest, User $user)
    {
        $this->httpRequest = $httpRequest;
        $this->user = $user;
    }

    public function process(callable $next)
    {
        $token = $this->httpRequest->getHeader('Authorization');
        if (!$token || !preg_match('/Bearer\s+(.+)/', $token, $matches)) {
            return new JsonResponse(['error' => 'Unauthorized']); //, \Nette\Http\IResponse::S401_Unauthorized
        }

        // Ověření tokenu (Base64 decode)
        $decoded = json_decode(base64_decode($matches[1]), true);
        if (!$decoded || !isset($decoded['username']) || $decoded['exp'] < time()) {
            return new JsonResponse(['error' => 'Invalid token']); //, \Nette\Http\IResponse::S401_UNAUTHORIZED
        }

        // Přihlášení uživatele
        try {
            $this->user->login($decoded['username'], 'vokurka');
        } catch (\Nette\Security\AuthenticationException $e) {
            return new JsonResponse(['error' => 'Unauthorized']); //, \Nette\Http\IResponse::S401_UNAUTHORIZED
        }

        return $next();
    }
}
