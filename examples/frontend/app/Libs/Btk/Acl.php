<?php

namespace Btk;

use Nette\Security\Permission;
use Nette\Caching\Cache;

class Acl extends \Nette\Security\Permission {

    public function __construct(\App\Model\AclModel $AclModel)
    {
        $storage = new \Nette\Caching\Storages\FileStorage(APP_DIR . '/../temp/cache');
        $cache = new Cache($storage);

        $roles = $cache->load('acl-roles');
        if ($roles === NULL) {
            $roles = $AclModel->getRoles();
            $cache->save('acl-roles', $roles, array(
                Cache::EXPIRE => '7 days',
                Cache::SLIDING => TRUE,
            ));
        }

        foreach($roles as $role) {
            $this->addRole($role->name, $role->parent_name);
        }

        $resources = $cache->load('acl-resources');
        if ($resources === NULL) {
            $resources = $AclModel->getResources();
            $cache->save('acl-resources', $resources, array(
                Cache::EXPIRE => '7 days',
                Cache::SLIDING => TRUE,
            ));
        }

        foreach($resources as $resource) {
            $this->addResource($resource->name);
        }

        $rules = $cache->load('acl-rules');
        if ($rules === NULL) {
            $rules = $AclModel->getRules();
            $cache->save('acl-rules', $rules, array(
                Cache::EXPIRE => '7 days',
                Cache::SLIDING => TRUE,
            ));
        }

        foreach($rules as $rule) {
            $rule->resource     = $rule->resource   == 'ALL' ? Permission::ALL : $rule->resource;
            $rule->privilege    = $rule->privilege  == 'ALL' ? Permission::ALL : $rule->privilege;

            $this->{$rule->allowed == 'Y' ? 'allow' : 'deny'}($rule->role, $rule->resource, $rule->privilege);
        }
    }
}