<?php

namespace Btk;

use Nette\Utils\Image;

/**
 * Class with helpers for better life with this application
 *
 * @author Tomas Kotasek
 */



class Helpers
{

    /**
     * Function convert length of time in string to seconds
     *
     * @param   string  $timeString     time in string like 2 days, 7 weeks etc.
     * @return  int                     seconds
     */

    public function formatTimeLengthToSeconds(string $timeString)
    {
        $time           = new \DateTime($timeString);
        $currentTime    = new \DateTime();

        return intval(abs($time->format('U') - $currentTime->format('U')));
    }


    /**
     * Function convert name to webalize form for URL
     *
     * @param   string  $title
     * @return  string                     seconds
     */
    public static function getSeoTitle(string $title)
    {
        return \Nette\Utils\Strings::webalize($title);
    }

    public static function formatPrice($price, $decimals = 0)
    {
        return number_format($price, $decimals, ' ', ' ');
    }

    public static function getimagelink($id, $type, $suffix = '', $file =  false)
    {
        $first = substr($id, 0, 1);
        if ($file === true) {
            $file = WWW_DIR;
        }

        $file .= '/upload/'.$type.'/'.$first.'/';

        if (! empty($suffix)) {
            $file .= $suffix.'/'.$id.'_'.$suffix.'.jpg';
        } else {
            $file .= $id.'.jpg';
        }

        return $file;
    }

    public static function kwToHP($kw)
    {
        $convert = 1.3596216173039;

        return round($kw * $convert,0);
    }

    public static function getprice($product, $convertRate, $precision = 0, $vat = null)
    {
        $price = round(($product->price / $convertRate) * (($product->commission / 100) + 1), $precision);

        if (empty($vat)) {
            return $price;
        }

        $priceWithVat = round($price * (($vat / 100) + 1), $precision);

        return $priceWithVat;
    }

    public static function getDeliveryBadge($supplier)
    {
        if (in_array($supplier, [1, 4, 10])) {
            return '<span class="deliveryBadge express"> Expresní dodání </span>';
        } else if  (in_array($supplier, [2, 6, 9, 11])) {
            return '<span class="deliveryBadge normal">Běžná doba dodání</span>';
        } else {
            return '<span class="deliveryBadge bad">Doba dodání <br /> se může prodloužit</span>';
        }
    }

    /**
     * Check if exist image on drive. If not - image is saved
     *
     * @param string $webserviceDocumentsUrl
     * @param object $product
     * @return boolean true - images exists, false - image was new created, need to be saved into database
     */
    public static function checkImage(string $webserviceDocumentsUrl, $product)
    {
        $imgPath = self::getTecDocImgPath($product->idProduct, true);

        if (!file_exists(WWW_DIR.$imgPath)) {
            self::saveProductImageToFile($webserviceDocumentsUrl, $product->idProduct, $product->articleDocuments->docId);
            return false;
        }

        return true;
    }

    public static function getTecDocImgPath(int $idProduct, bool $thumb = false, bool $onlyFolder = false, bool $createFolders = false)
    {
        $path = '/'.implode('/', str_split($idProduct)).'/';

        if ($thumb === true) {
            $prefix = 'upload/td_thumb';
        } else {
            $prefix = 'upload/td_images';
        }

        $suffix = '';
        if ($onlyFolder === false) {
            $suffix = $idProduct.'.jpg';
        }

        if ($createFolders === true) {
            if (!file_exists($prefix.$path)) {
                mkdir($prefix.$path, 0775, true);
            }
        }

        return $prefix.$path.$suffix;
    }

    public static function saveProductImageToFile(string $webserviceDocumentsUrl = null, int $idProduct = null, string $docId = null)
    {
        //$this->TecDoc->addDynamicAddress('188.75.141.74', 24);
        $file = $webserviceDocumentsUrl.'/'.$docId.'/0';

        try {
            $fileSource = file_get_contents($file);
        } catch (Exception $exc) {
            echo $exc->getTraceAsString();
        }

        // fullsize
        $image = Image::fromString($fileSource);
        self::getTecDocImgPath($idProduct, false, true, true);
        $image->save(self::getTecDocImgPath($idProduct), 80, Image::JPEG);

        // thumbnail
        $image->resize(205, 155, Image::EXACT);
        self::getTecDocImgPath($idProduct, true, true, true);
        $image->save(self::getTecDocImgPath($idProduct, true), 80, Image::JPEG);

        return 1;
    }

        public static function getSQLDateTimeFromTS(int $ts = null)
    {
        if (empty($ts)) {
            return date('Y-m-d H:i:s', time());
        }
        return date('Y-m-d H:i:s', $ts);
    }

    public static function getSQLDateTimeFromInput(string $val = null)
    {
        if (empty($val)) {
            return null;
        }

        $ts = strtotime($val);

        return date('Y-m-d H:i:s', $ts);
    }

    public static function getDateForInput(string $dateTime = null)
    {
        if (empty($dateTime)) {
            return null;
        }

        return date('Y-m-d', strtotime($dateTime));
    }


    public static function saltPassword($pass, $nick, $salt)
    {
        return md5($pass).md5($nick).md5($salt);
    }

}