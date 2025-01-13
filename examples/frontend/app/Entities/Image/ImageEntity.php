<?php

declare(strict_types = 1);

namespace Entities;

use \Dibi\DateTime;

/**
 * Description of entity Image.
 * Class for define object of image.
 *
 * @author Tomas Kotasek
 */

class ImageEntity extends Entity
{
	/**
	 * Main element ID
	 *
	 * @var int
	 */
	public ?int 			$idImage = null;

	/**
	 * Name of file on disk
	 *
	 * @var string
	 */
	public string			$image;

	/**
	 * Captured date of picture
	 *
	 * @var DateTime
	 */
	public ?DateTime 		$capturedDate = null;

	/**
	 * Link to the Instagram to the detail of this photo
	 *
	 * @var string
	 */
	public ?string			$instalink = null;

	/**
	 * Orientation / type of image one of
	 * portrait, landscape, square, panorama
	 *
	 * @var string
	 */
	public string			$type;

	/**
	 * GPS position of location
	 *
	 * @var string
	 */
	public ?string			$location = null;

	/**
	 * Show this picture on HP in slider
	 *
	 * @var int
	 */
	public int				$showOnHp;

	/**
	 * This picture can be sold as print
	 *
	 * @var int
	 */
	public int				$forSale;

	/**
	 * Is this picture visible
	 *
	 * @var int
	 */
	public int				$published;

	/**
	 * Integer value of position in ordered list
	 *
	 * @var int
	 */
	public int				$sorting;

	/**
	 * String shortcut for location
	 *
	 * @var string
	 */
	public string			$locale;

	/**
	 * Name of the picture
	 *
	 * @var string
	 */
	public string			$title = '';

	/**
	 * Seo title of the picture
	 *
	 * @var string
	 */
	public string			$seoTitle;

	/**
	 * Longer description of picture
	 *
	 * @var string
	 */
	public string 			$perex;

	/**
	 * Date and time of uploaded image to system
	 *
	 * @var DateTime
	 */
	public DateTime 		$uploaded;


	/**
	 * Name of location
	 *
	 * @var string
	 */
	public string			$locationName;

	/**
	 * Main collection tag
	 *
	 * @var int
	 */
	public ?int				$mainTag;

	public function __construct(array $detail = null)
	{
		if (! empty($detail)) {
			$this->fill($detail);
		}
	}

	/**
	 * Fill object with data if image detail is set on construct.
	 *
	 * @param array $detail
	 */
	public function fill(array $detail)
	{
		foreach ($detail as $k => $v) {
			if ($v !== null) {
				$this->$k = $v;
			}

			if ($k == 'title') {
				$this->setSeoTitle($v);
			}
		}
	}

	/**
	 * Return image detail data with localized texts
	 *
	 * @param int $idImage
	 * @param string $locale
	 */

	public function getImageDetail(int $idImage, string $locale)
	{

	}


	/**
	 * Set SEO title.
	 *
	 * @param string $title
	 */
	private function setSeoTitle(string $title)
	{
		$this->seoTitle = \Btk\Helpers::getSeoTitle($title);
	}



}