#!/bin/bash
set -e

cat /etc/*-release

P_VERSION=$(python3 --version)

if [[ "$P_VERSION" != "Python 3.10.9" ]]; then
	echo "Python 3.10.9 missing. Trying to install it"
	sudo yum update -y && sudo yum upgrade -y
    sudo yum install -y make gcc perl-core pcre-devel wget zlib-devel
    wget https://www.openssl.org/source/openssl-1.1.1k.tar.gz
    tar -xzvf openssl-1.1.1k.tar.gz
    cd openssl-1.1.1k
    ./config --prefix=/usr --openssldir=/etc/ssl --libdir=lib no-shared zlib-dynamic
    make
    sudo make install
    
    sudo yum groupinstall "Development Tools" -y
    sudo yum install -y openssl11-devel bzip2-devel libffi-devel
    wget https://www.python.org/ftp/python/3.10.9/Python-3.10.9.tar.xz
    tar -xf Python-3.10.9.tar.xz
    cd Python-3.10.9
    make clean
    sed -i 's/PKG_CONFIG openssl /PKG_CONFIG openssl11 /g' configure
    ./configure --enable-optimizations
    make -j 4  # Adjust '4' to the number of cores in your processor for faster compilation
    sudo make altinstall
    sudo alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 1
    sudo alternatives --set python3 /usr/local/bin/python3.10
    python3 -m ensurepip --upgrade
    
    echo "$(python3 --version) available"
else 
	echo "$P_VERSION available"
fi