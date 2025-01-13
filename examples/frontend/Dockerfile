# Base image s PHP 8.3 a Apache
FROM php:8.3-apache

ENV TZ=Europe/Prague

RUN docker-php-ext-install mysqli

RUN apt-get update -y && apt-get install -y \
	libwebp-dev \
	libjpeg62-turbo-dev \
	libpng-dev \
	libxpm-dev \
	libfreetype6-dev \
	libonig-dev \
	libzip-dev \
	zlib1g-dev \
    zip \
	unzip \
	libicu-dev

RUN docker-php-ext-install mbstring
RUN docker-php-ext-install exif

# GD
RUN docker-php-ext-configure gd --with-freetype --with-jpeg && docker-php-ext-install -j "$(nproc)" gd
RUN #docker-php-ext-configure gd --with-freetype=/usr/include/ --with-jpeg=/usr/include/ \ && docker-php-ext-install gd

# Instalace Composeru
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Aktivace mod_rewrite pro Nette
RUN a2enmod rewrite

# Nastavení pracovního adresáře
WORKDIR /var/www/html/

# Nastavení práv pro PHP aplikaci
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html

# Expozice portu 80
EXPOSE 80