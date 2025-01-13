<?php

declare(strict_types = 1);

namespace App\Model;

use Nette;
use Nette\Caching\Cache;

class BaseModel
{
    use \Nette\SmartObject;

    public string 	$tableName			= '';
    protected 		$db;

	/**
	 * @var Nette\Caching\Cache
	 */
	protected $cache;

	/**
     * @param \Dibi\Connection $db
     */
    function __construct(\Dibi\Connection $db, \Nette\Caching\Storage $storage)
    {
        $this->db 				= $db;
		$this->cache    		= new Cache($storage);
    }

    /**
     *
     * @param int $start
     * @param int $count
     * @param array $attrs
     * @param array $filter
     * @param array $order
     * @return type
     */
    protected function getListParent(int $start = 0, int $count = -1, array $attrs = [],
        array $filter = [], array $order = [])
    {
        $sql_attrs = $this->getAttrs($attrs);

        $obj = $this->db->select($sql_attrs)->from($this->tableName);

        $this->getFilter($obj, $filter);

        if ($start != 0) {
            $obj->offset($start);
        }
        if ($count != -1) {
            $obj->limit($count);
        }

        if (!empty($order)) {
            $obj->orderBy($order);
        }

        return $obj;
    }

    /**
     *
     * @param int $start
     * @param int $count
     * @param array $attrs
     * @param array $filter
     * @param array $order
     * @return type
     */
    public function getList(int $start = 0, int $count = -1, array $attrs = [],
        array $filter = [], array $order = [])
    {
        return $this->getListParent($start, $count, $attrs, $filter, $order)
            ->fetchAll();
    }

    /**
     *
     * @param int $start
     * @param int $count
     * @param array $attrs
     * @param array $filter
     * @param array $order
     * @param string $key
     * @param string $value
     * @return type
     */
    public function getListForSelect(int $start = 0, int $count = -1, array $attrs = [],
        array $filter = [], array $order = [], string $key = 'id', string $value = 'title')
    {
        return $this->getListParent($start, $count, $attrs, $filter, $order)
            ->fetchPairs($key, $value);
    }

    /**
     *
     * @param int $id
     * @param array $attrs
     * @param string $idColumn
     * @param string $idType
     * @return type
     */
    public function getAttributes($id, array $attrs = [], string $idColumn = 'id',
        string $idType = 'i')
    {
        $sql_attrs = $this->getAttrs($attrs);

        return $this->db->select(
            $sql_attrs.' FROM ['.$this->tableName.'] WHERE ['.$idColumn.'] = %'.$idType,
            $id
        )->fetch();
    }

    /**
     *
     * @param array $data
     * @return type
     */
    public function create($data)
    {
        $this->db->query('INSERT INTO ['.$this->tableName.']', $data);
        return $this->db->getInsertId();
    }

    /**
     *
     * @param array $data
     * @return type
     */
    public function createWoId($data)
    {
        return $this->db->query('INSERT INTO ['.$this->tableName.']', $data);
    }

    /**
     *
     * @param array $data
     * @return type
     */
    public function insertIgnore($data)
    {
        return $this->db->query('INSERT IGNORE INTO ['.$this->tableName.']', $data);
    }

    /**
     *
     * @param array $data
     * @return type
     */
    public function insertOnDuplicateUpdate($data)
    {
        return $this->db->query('INSERT INTO ['.$this->tableName.'] %v ON DUPLICATE KEY UPDATE %a', $data, $data);
    }

    /**
     *
     * @param string or int $id
     * @param array $data
     * @param string $idColumn
     * @param string $idType
     * @return type
     */
    public function edit($id, $data, string $idColumn = 'id', string $idType = 'i')
    {
        return $this->db->query(
            'UPDATE ['.$this->tableName.'] SET ', $data,
            'WHERE ['.$idColumn.'] = %'.$idType, $id
        );
    }

    /**
     *
     * @param array $data
     * @param string $idColum
     * @param string $idType
     * @return type
     */
    public function save($data, string $idColum = 'id', string $idType = 'i')
    {
        if (empty($data[$idColum])) {
            unset($data[$idColum]);

            return $this->create($data, $idColum);
        } else {
            $id = $data[$idColum];
            unset($data[$idColum]);

            $this->edit($id, $data, $idColum, $idType);
        }
    }

    /**
     *
     * @param int $id
     * @param string $idColumn
     * @return type
     */
    public function delete(int $id, string $idColumn = 'id')
    {
        if (isset($this->translationsTable)) {
            $this->removeTranslations($id, $idColumn);
        }
        return $this->db->query('DELETE FROM ['.$this->tableName.']
            WHERE ['.$idColumn.'] = %i', $id);
    }

    /**
     *
     * @param array $filter
     * @return type
     */
    public function getCount(array $filter = [])
    {
        $obj = $this->db->select('COUNT(*)')->from($this->tableName);
        $this->getFilter($obj, $filter);

        return $obj->fetchSingle();
    }


    protected function getFilter(&$obj, array $filter)
    {
        if (!empty($filter)) {
            foreach ($filter as $key => $value) {
                $type = 's';
                $foo = '=';
                if (is_int($value)) {
                    $type = 'i';
                } elseif (is_array($value)) {
                    $type = 'l';
                    $foo = 'IN';
                } elseif ($value == 'IS NOT NULL') {
                    $obj->where('['.$key.'] != ""');
                    $obj->where('['.$key.'] != "0"');
                    $type = 'sql';
                    $foo = '';
                } elseif ($value == 'IS NULL') {
                    $type = 'sql';
                    $foo = '';
                } elseif (strstr($value, 'LIKE')) {
                    $type = 's';
                    $value = trim(str_replace('LIKE', '', $value));
                    $obj->where('['.$key.'] LIKE "%'.$value.'%"');
                    return;
                } elseif (strstr($key, '>')) {
                    $key = trim(str_replace('>', '', $key));
                    $obj->where('['.$key.'] > %i', $value);
                    return;
                } elseif (strstr($key, '<')) {
                    $key = trim(str_replace('<', '', $key));
                    $obj->where('['.$key.'] < %i', $value);
                    return;
                } elseif (strstr($key, '!=')) {
                    $key = trim(str_replace('!=', '', $key));
                    $obj->where('['.$key.'] != %i', $value);
                    return;
                }

                $obj->where('['.$key.'] '.$foo.' %'.$type, $value);
            }
        }
    }

    protected function getAttrs($attrs)
    {
        $sql_attrs = '';
        if (!empty($attrs)) {
            $i = 1;
            $attrsCount = count($attrs);
            foreach ($attrs as $attr) {
                if (!empty($sql_attrs)) {
                    $sql_attrs .= ' ';
                }
                $sql_attrs .= $attr;
                if ($i < $attrsCount) {
                    $sql_attrs .= ',';
                }
                $i++;
            }
        } else {
            $sql_attrs = '*';
        }

        return $sql_attrs;
    }

    public function getSeoTitle($title)
    {
        $new_seo_title = \Nette\Utils\Strings::webalize($title);

        $detail = $this->getAttributes($new_seo_title, [], 'title_seo', 's');

        if (! empty($detail)) {
            $new_seo_title = $this->getSeoTitle($detail['title_seo'].' 1');
        }

        return $new_seo_title;
    }

    public function query($sql)
    {
        return $this->db->query($sql);
    }

	public function getDefaultList(int $start = 0, int $limit = -1, array $filter = [], array $order = [], array $itemsToTranslations = [])
    {
        $obj = $this->prepareQueryForDefaultList($itemsToTranslations);

        if (! empty($order)) {
            $obj->orderBy($order);
        }

        foreach ($filter as $key => $item) {
            $this->getFilter($obj, [$key => $item]);
        }

        return $obj->fetchAll($start, $limit);
    }

//    public function prepareQueryForDefaultList()
//    {
//		return $obj = $this->db->select("*")->from($this->tableName);
//	}

// slepa vyvojova vetev ze by se prelozene zaznamy ukazovaly v jednom radku.
// musel by se predelat system ukladani dat atd.. zbytecne v automatizaci, lze predelat pri samostatne uprave presenteru
	public function prepareQueryForDefaultList(array $itemsToTranslations = [])
	{
		if (empty($itemsToTranslations) || empty($this->translateJoinId)) {
			return $obj = $this->db->select("*")
				->from($this->tableName);
		}

		$select = "T.*";
		foreach ($this->langList as $langKey => $lang) {
			foreach ($itemsToTranslations as $item) {
				$select .= ",(SELECT $item FROM $this->translationsTable AS TT WHERE TT.locale = '".$langKey."' AND TT.$this->translateJoinId = T.$this->translateJoinId) AS ".$item."_".$langKey;
			}
		}
//		dump($select);
//		die("File:" . __FILE__ . "; Line:" . __LINE__);
		$query = $this->db->select($select)
			->from($this->tableName . " AS T");
//			->leftJoin($this->translationsTable . " AS TT")
//			->on("TT.$this->translateJoinId = T.$this->translateJoinId");

		return $query;
	}

    public function getDefaultListCount(array $filter = [])
    {
        $obj = $this->prepareQueryForDefaultListCount();
        foreach ($filter as $key => $item) {
            $this->getFilter($obj, [$key => $item]);
        }

        return $obj->fetchSingle();
    }

    public function prepareQueryForDefaultListCount()
    {
        return $this->db->select('COUNT(*)')->from($this->tableName);
    }

    public function saveTranslationData($values, string $idKey, array $languages, array $itemsToTranslations)
    {
        $translationsToSave = [];

		foreach ($languages AS $langKey => $langItem) {
			$translationsToSave[$langKey] = ['locale'    => $langKey];

			foreach ($itemsToTranslations AS $key => $item) {

				if (isset($values[$item.'_'.$langKey])) {
					$translationsToSave[$langKey][$item] = $values[$item.'_'.$langKey];
					unset($values[$item.'_'.$langKey]);
				}
			}
        }

        if (empty($values[$idKey])) {
            unset($values[$idKey]);

            $id = $this->create($values, $idKey);
        } else {
            $id = $values[$idKey];
            unset($values[$idKey]);

            $this->edit($id, $values, $idKey, 'i');
        }

        foreach ($translationsToSave as $key => $item) {
            $transData = array_merge($item, [$idKey => $id]);
            $this->db->query('INSERT INTO ['.$this->translationsTable.'] %v ON DUPLICATE KEY UPDATE %a', $transData, $transData);
        }

        return $id;
    }

    public function getDataForTranslationById(int $id, string $idParam, array $languages, array $translatedItems)
    {
        $sql = '';

        foreach ($languages as $langKey => $lang) {

            foreach ($translatedItems as $item) {
                $query = sprintf(", (SELECT %s FROM [$this->translationsTable] WHERE ".$idParam." = %d AND locale = '%s') AS %s_%s", $item, $id, $langKey, $item, $langKey);
                $sql .= $query;
            }
        }

        return $this->db->select("* %sql", $sql)
            ->from($this->tableName)
            ->where($idParam." = %i", $id)
            ->fetch();
    }

    public function getDetail($id, $idColumn, $locale)
    {
        return $this->getAttributes($id, [], $idColumn);
    }

    public function removeTranslations($id, $idColumn)
    {
        return $this->db->query('DELETE FROM ['.$this->translationsTable.']
            WHERE ['.$idColumn.'] = %i', $id);
    }
}