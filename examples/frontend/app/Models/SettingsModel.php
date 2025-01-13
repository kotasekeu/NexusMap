<?php

declare(strict_types = 1);

namespace App\Model;

class SettingsModel extends BaseModel
{
    public string $tableName = 'settings';

    /**
     *
     * @return type
     */
    public function getMainData(string $locale)
    {
        $data = $this->db->select("`key`, `value`")
                ->from($this->tableName)
                ->where('`main` = %i', 1)
                ->where('`locale` = %s OR `locale` = %s', $locale, 'all')
                ->fetchPairs('key', 'value');

        foreach ($data as $key => $item) {
            if (strpos($key, "_".$locale)) {
                $data[str_replace('_'.$locale, '', $key)] = $item;
                unset($data[$key]);
            }
        }

        return (object)$data;
    }

    /**
     * getSalts
     *
     * Return object with salts for login
     *
     * @return object
     */
    public function getSalts()
    {
        return (object)$this->getListForSelect(0, -1, [], ['key' => ['adminSalt', 'frontSalt']], [], 'key', 'value');
    }

    public function getInstaData()
    {
        return (object)$this->getListForSelect(0, -1, [], ['key' => ['instaApiKey', 'instaApiSecret']], [], 'key', 'value');
    }

	/*
	 * @return string Admin Salt required for correct create password and login into admin.
	 */
	public function getAdminSalt() : string
	{
		return $this->db->select("value")
			->from($this->tableName)
			->where("`key` = %s", 'adminSalt')
			->fetchSingle();
	}
}
