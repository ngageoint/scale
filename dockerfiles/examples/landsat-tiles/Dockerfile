FROM geoint/landsat-base
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

LABEL com.ngageoint.scale.job-type="{\"name\":\"landsat-tiles\",\"version\":\"1.0.0\",\"title\":\"Landsat Tiles\",\"description\":\"Generate map tiles for a landsat 8 product.\",\"author_name\":\"tclarke@ball.com\",\"docker_image\":\"geoint/landsat-tiles\",\"priority\":250,\"timeout\":300,\"max_tries\":3,\"cpus_required\":0.5,\"mem_required\":512,\"interface\":{\"version\":\"1.0\",\"command\":\"./landsat_tiles.sh\",\"command_arguments\":\"$ {image} $ {job_output_dir}\",\"input_data\":[{\"name\":\"image\",\"type\":\"file\",\"required\":true,\"media_types\":[\"image/tiff\"]}],\"output_data\":[{\"name\":\"tiles\",\"type\":\"files\",\"required\":true}]}}"

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
