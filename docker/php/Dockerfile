FROM php:8.4-apache

ENV TZ=Europe/Prague

# Povolení Apache modulů
RUN a2enmod rewrite headers

# Instalace PHP rozšíření
RUN apt-get update -y && apt-get install -y \
    libwebp-dev \
    libjpeg62-turbo-dev \
    libpng-dev \
    libxpm-dev \
    libfreetype6-dev \
    libonig-dev \
    libzip-dev \
    zlib1g-dev \
    libicu-dev \
    git \
    unzip && \
    docker-php-ext-install mysqli mbstring zip calendar intl && \
    docker-php-ext-configure gd --with-freetype --with-jpeg && docker-php-ext-install -j "$(nproc)" gd && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalace Composeru
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Nastavení pracovního adresáře
WORKDIR /var/www/html/

# Nastavení práv pro PHP aplikaci
RUN chown -R www-data:www-data /var/www/html && chmod -R 755 /var/www/html

# Expozice portu 80
EXPOSE 80