FROM geoint/landsat-base
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

USER root
RUN yum install -y gdal-devel boost-devel \
 && yum clean all \
 && git clone https://github.com/gina-alaska/dans-gdal-scripts.git \
 && cd dans-gdal-scripts \
 && ./autogen.sh \
 && ./configure \
 && make \
 && make install \
 && cd .. \
 && rm -rf dans-gdal-scripts
COPY landsat_tiles.sh ./
ENTRYPOINT ["./landsat_tiles.sh"]
