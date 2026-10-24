FROM debian:13.4-slim

USER root
WORKDIR /var/webmaboss


## -----------------------------------------------------------------------------------------------
## distribution packages
##
RUN apt-get update -qq && \
    apt-get install -yq --no-install-recommends ca-certificates wget pkg-config \
                          python3 python3-dev python3-pip \
                          curl \
                          #software-properties-common \
                          nano git apt-transport-https \
                          apache2 apache2-dev mariadb-client libmariadb-dev graphviz unzip \
                          flex bison g++ make cmake libxml2-dev libbz2-dev zlib1g-dev \
    && apt-get clean -y 
##-----------------------------------------------------------------------------------------------
## base conda environment
## 
## Exact versions of all conda packages (python, GINsim, MaBoSS...) are listed in docker/conda-linux-64.lock
## It is installed without solving, so rebuilding the image always gives the same environment.
## To update it : install the new packages in an image, and export them with 'conda list --explicit --md5'
ADD docker/conda-linux-64.lock /tmp/conda-linux-64.lock
RUN wget --quiet https://github.com/mamba-org/micromamba-releases/releases/download/2.9.0-0/micromamba-linux-64 -O /usr/local/bin/micromamba \
    && chmod +x /usr/local/bin/micromamba \
    && micromamba create -y -p /opt/conda --file /tmp/conda-linux-64.lock \
    && micromamba clean -y --all && rm -rf /opt/conda/pkgs /tmp/conda-linux-64.lock /root/.cache/mamba

ENV PATH="${PATH}:/opt/conda/bin"

# GINsim 3.1.post20261018 requires Java >= 25, which forbids the py4j 0.10.9.5 bundled in GINsim.jar
# from iterating over Java collections (InaccessibleObjectException) : biolqm.fixpoints and the other
# tools would silently return nothing. Can be removed once the GINsim launcher or its py4j handles it.
ENV JDK_JAVA_OPTIONS="--add-opens=java.base/java.util=ALL-UNNAMED"

## -----------------------------------------------------------------------------------------------
## NodeJS & Yarn install, only used to build the javascript of the interface
##
RUN curl -sL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs=24.21.0-1nodesource1 \
    && apt clean -y \
    && npm install -g yarn@1.22.22

## -----------------------------------------------------------------------------------------------
## Installing libSBML
##
# RUN wget https://github.com/sbmlteam/libsbml/archive/refs/tags/v5.20.2.tar.gz \
#     && tar -zxf v5.20.2.tar.gz \
#     && cd libsbml-5.20.2 \
#     && mkdir build \
#     && cd build \
#     && cmake -DCMAKE_INSTALL_PREFIX=/usr \
#         -DCMAKE_INSTALL_LIBDIR=/usr/lib \
#         -DCMAKE_CXX_COMPILER=g++ \
#         -DCMAKE_C_COMPILER=gcc \
#         -DCMAKE_CXX_STANDARD_LIBRARIES=-lxml2 \
#         -DWITH_SWIG=OFF \
#         -DLIBXML_LIBRARY=/usr/lib/x86_64-linux-gnu/libxml2.so \
#         -DLIBXML_INCLUDE_DIR=/usr/include/libxml2 \
#         -DENABLE_COMP=ON \
#         -DENABLE_FBC=ON \
#         -DENABLE_GROUPS=ON \
#         -DENABLE_LAYOUT=ON \
#         -DENABLE_MULTI=ON \
#         -DENABLE_QUAL=ON \
#         -DENABLE_RENDER=ON \
#         -DENABLE_DISTRIB=ON \
#         .. \
#     && make \
#     && make install \
#     && cd ../.. \
#     && rm -fr libsbml-5.20.2 v5.20.2.tar.gz

# ## -----------------------------------------------------------------------------------------------
# ## Installing MaBoSS from github repo
# ##
# RUN git clone https://github.com/sysbio-curie/MaBoSS /opt/MaBoSS \
#     && cd /opt/MaBoSS/engine/src/ \
#     && make install SBML_COMPAT=1 \
#     && make MAXNODES=128 SBML_COMPAT=1 install \
#     && make MAXNODES=256 SBML_COMPAT=1 install \
#     && make MAXNODES=512 SBML_COMPAT=1 install \
#     && make MAXNODES=1024 SBML_COMPAT=1 install \
#     && mv /opt/MaBoSS/engine/pub/MaBoSS /opt/conda/bin \
#     && mv /opt/MaBoSS/engine/pub/MaBoSS_128n /opt/conda/bin \
#     && mv /opt/MaBoSS/engine/pub/MaBoSS_256n /opt/conda/bin \
#     && mv /opt/MaBoSS/engine/pub/MaBoSS_512n /opt/conda/bin \
#     && mv /opt/MaBoSS/engine/pub/MaBoSS_1024n /opt/conda/bin \
#     && cd ../python \
#     && cp -r ../src cmaboss/ \
#     && /opt/conda/bin/python3 -m pip install --upgrade wheel setuptools numpy \
#     && /opt/conda/bin/python3 -m pip install . \
#     && rm -fr /opt/MaBoSS \
#     && ls /var/ \
#     && ls /var/webmaboss
ADD requirements.txt docker/constraints.txt /var/webmaboss/
RUN /opt/conda/bin/python3 -m pip install -c /var/webmaboss/constraints.txt --upgrade wheel setuptools numpy
RUN /opt/conda/bin/python3 -m pip install --no-cache-dir -c /var/webmaboss/constraints.txt --upgrade -r /var/webmaboss/requirements.txt
# Exposing port 8000 for server access
EXPOSE 8000



ADD api /var/webmaboss/api
ADD frontend /var/webmaboss/frontend
ADD settings /var/webmaboss/settings
ADD create_default_db.sh create_default_admin.sh install.sh maintenance.sh runserver.sh wait_db.sh /var/webmaboss/
ADD .babelrc LICENSE.md manage.py package.json yarn.lock webpack.config.js /var/webmaboss/

# Downloading node modules with the exact versions of yarn.lock, and building the javascript (production mode)
RUN mkdir node_modules \
    && yarn install --frozen-lockfile \
    && npm run build

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
    && rm -rf /var/webmaboss/node_modules/* \
    && rm -rf /opt/conda/pkgs/*



# Switching to apache user
USER www-data

# Running server
# The maintenance (manage.py maintenance) runs in the background, every MAINTENANCE_EVERY seconds (0 : never)
CMD /var/webmaboss/wait_db.sh; \
    /bin/bash /var/webmaboss/create_default_db.sh --settings=settings.prod_settings; \
    /bin/bash /var/webmaboss/maintenance.sh & \
    /var/webmaboss/server/apachectl -D FOREGROUND

