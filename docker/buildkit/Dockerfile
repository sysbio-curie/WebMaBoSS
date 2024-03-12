FROM debian:12.5-slim AS webmaboss-base

USER root
WORKDIR /var/webmaboss


## -----------------------------------------------------------------------------------------------
## distribution packages
##
RUN apt-get update -qq && \
    apt-get install -yq --no-install-recommends ca-certificates wget pkg-config \
                          python3 python3-dev python3-pip \
                          curl software-properties-common nano git apt-transport-https \
                          apache2 apache2-dev mariadb-client libmariadb-dev graphviz unzip \
                          flex bison g++ make cmake libxml2-dev libbz2-dev zlib1g-dev \
    && apt-get clean -y \
##-----------------------------------------------------------------------------------------------
## base conda environment
## 
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py312_24.1.2-0-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh 
    
ENV PATH="${PATH}:/opt/conda/bin"

RUN conda config --set auto_update_conda False \
    && conda install --no-update-deps -y \
        -c colomoto -c conda-forge ginsim \
    && conda clean -y --all && rm -rf /opt/conda/pkgs

## -----------------------------------------------------------------------------------------------
## NodeJS & Yarn install
##
RUN curl -sL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt clean -y \
    && npm install -g yarn

## -----------------------------------------------------------------------------------------------
## Installing libSBML
##
RUN wget https://github.com/sbmlteam/libsbml/archive/refs/tags/v5.20.2.tar.gz \
    && tar -zxf v5.20.2.tar.gz \
    && cd libsbml-5.20.2 \
    && mkdir build \
    && cd build \
    && cmake -DCMAKE_INSTALL_PREFIX=/usr \
        -DCMAKE_INSTALL_LIBDIR=/usr/lib \
        -DCMAKE_CXX_COMPILER=g++ \
        -DCMAKE_C_COMPILER=gcc \
        -DCMAKE_CXX_STANDARD_LIBRARIES=-lxml2 \
        -DWITH_SWIG=OFF \
        -DLIBXML_LIBRARY=/usr/lib/x86_64-linux-gnu/libxml2.so \
        -DLIBXML_INCLUDE_DIR=/usr/include/libxml2 \
        -DENABLE_COMP=ON \
        -DENABLE_FBC=ON \
        -DENABLE_GROUPS=ON \
        -DENABLE_LAYOUT=ON \
        -DENABLE_MULTI=ON \
        -DENABLE_QUAL=ON \
        -DENABLE_RENDER=ON \
        -DENABLE_DISTRIB=ON \
        .. \
    && make \
    && make install \
    && cd ../.. \
    && rm -fr libsbml-5.20.2

## -----------------------------------------------------------------------------------------------
## Installing MaBoSS from github repo
##
RUN git clone https://github.com/sysbio-curie/MaBoSS /opt/MaBoSS \
    && cd /opt/MaBoSS/engine/src/ \
    && make install SBML_COMPAT=1 \
    && make MAXNODES=128 SBML_COMPAT=1 install \
    && make MAXNODES=256 SBML_COMPAT=1 install \
    && make MAXNODES=512 SBML_COMPAT=1 install \
    && make MAXNODES=1024 SBML_COMPAT=1 install \
    && mv /opt/MaBoSS/engine/pub/MaBoSS /opt/conda/bin \
    && mv /opt/MaBoSS/engine/pub/MaBoSS_128n /opt/conda/bin \
    && mv /opt/MaBoSS/engine/pub/MaBoSS_256n /opt/conda/bin \
    && mv /opt/MaBoSS/engine/pub/MaBoSS_512n /opt/conda/bin \
    && mv /opt/MaBoSS/engine/pub/MaBoSS_1024n /opt/conda/bin \
    && cd ../python \
    && cp -r ../src cmaboss/ \
    && /opt/conda/bin/python3 -m pip install --upgrade wheel setuptools numpy \
    && /opt/conda/bin/python3 -m pip install . \
    && rm -fr /opt/MaBoSS
    
ADD requirements.txt /var/webmaboss/requirements.txt
RUN /opt/conda/bin/python3 -m pip install --no-cache-dir --upgrade -r /var/webmaboss/requirements.txt

# Exposing port 8000 for server access
EXPOSE 8000


FROM webmaboss-base AS webmaboss-base-with-test
# -------------------------------------------------------------------------------------------------
# Test environment : Firefox, Geckodriver, Chrome, Chromedriver
RUN \
    # Google chrome sources
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google.list \
    # Firefox sources
    # && echo "deb http://http.debian.net/debian unstable main" | tee /etc/apt/sources.list.d/debian-unstable.list \
    && apt-get -qq update \
    && apt-get install -y --no-install-recommends google-chrome-stable firefox-esr \
    && apt clean -y

    
    
RUN \
    # Installing chromedriver
    wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin \
    && chmod 775 /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

RUN \
    # Installing geckodriver
    wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz \
    && tar xvfz geckodriver-v0.34.0-linux64.tar.gz \
    && mv geckodriver /usr/local/bin \
    && rm geckodriver-v0.34.0-linux64.tar.gz

RUN \
    # Installing selenium
    /opt/conda/bin/python3 -m pip install --no-cache-dir --upgrade selenium

FROM webmaboss-base-with-test AS webmaboss-dev

CMD bash -c "tail -f /dev/null"

FROM webmaboss-base AS webmaboss

ADD api /var/webmaboss/api
ADD frontend /var/webmaboss/frontend
ADD settings /var/webmaboss/settings
ADD create_default_db.sh create_default_admin.sh install.sh runserver.sh wait_db.sh /var/webmaboss/
ADD .babelrc LICENSE.md manage.py package.json requirements.txt webpack.config.js /var/webmaboss/

# Removing node modules, downloading them from scratch, and transpiling the JSX
RUN mkdir node_modules \
    && yarn \
    && npm run dev

# Removing old db and medias, creating a new one, with default user admin:admin
RUN mkdir -p data/media \
    && mkdir -p data/db \
    && mkdir -p data/settings \
    && mkdir -p static \
    && mkdir -p .config/matplotlib
    
# Removing old server, and creating it from scratch
RUN /opt/conda/bin/python3 manage.py runmodwsgi --setup-only \
                                --host 0.0.0.0 --port 8000 \
                                --user www-data --group www-data \
                                --server-root=server/ \
                                --settings=settings.prod_settings \
                                --url-alias /static static/ \
                                --url-alias /data/media media/ \
                                --reload-on-changes

RUN chown -R www-data:www-data settings data server static api/migrations frontend/migrations \
    && chown www-data:www-data . && chown www-data:www-data .config/matplotlib

RUN cp -r /var/webmaboss/node_modules/bootstrap/ /var/webmaboss/static \
    && cp -r /var/webmaboss/node_modules/jquery/ /var/webmaboss/static

# -------------------------------------------------------------------------------------------------
# Cleanup    
RUN rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/webmaboss/node_modules/* yarn.lock


# Switching to apache user
USER www-data

# Running server
CMD /var/webmaboss/wait_db.sh; \
    /bin/bash /var/webmaboss/create_default_db.sh --settings=settings.prod_settings; \
    /var/webmaboss/server/apachectl -D FOREGROUND

FROM webmaboss-base-with-test AS webmaboss-test

ADD . /var/webmaboss/

# Removing old db and medias, creating a new one, with default user admin:admin
RUN rm -fr /var/webmaboss/data/ /var/webmaboss/api/migrations/*.py && \
    ls /var/webmaboss/api && \
    mkdir -p /var/webmaboss/data/media && \
    mkdir -p /var/webmaboss/data/db && \
    mkdir -p /var/webmaboss/data/settings && \
    mkdir -p /var/webmaboss/static && \
    chown -R www-data:www-data /var/webmaboss/settings /var/webmaboss/data /var/webmaboss/static /var/webmaboss/api/migrations && chown www-data:www-data /var/webmaboss && \
    mkdir /home/www-data && \
    usermod -d /home/www-data www-data && \
    chown -R www-data:www-data /home/www-data

RUN yarn && \
    npm run dev

USER www-data

CMD bash -c "tail -f /dev/null"
