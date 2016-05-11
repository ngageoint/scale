FROM tclarke/opticks
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

LABEL com.ngageoint.scale.job-type="{\"name\":\"ace\",\"version\":\"1.2.0\",\"title\":\"Adaptive Cosine Estimation\",\"description\":\"Signature matching with ACE followed but clustering and centroid detection. Stores result in a PostGIS database.\",\"author_name\":\"Trevor R.H. Clarke \\u003ctclarke@ball.com\\u003e\",\"icon_code\":\"f0fb\",\"docker_image\":\"devdocker-reg.devnet.prv:5000/geoint/ace_1.2\",\"priority\":250,\"timeout\":300,\"max_tries\":2,\"cpus_required\":2,\"mem_required\":1024,\"interface\":{\"version\":\"1.0\",\"command\":\"./runOpticks.sh\",\"command_arguments\":\"$ {image} $ {signature} $ {job_output_dir} $ {pg_connect_string}\",\"input_data\":[{\"name\":\"image\",\"type\":\"file\",\"required\":true,\"media_types\":[\"image/tiff\"]},{\"name\":\"signature\",\"type\":\"file\",\"required\":true},{\"name\":\"pg_connect_string\",\"type\":\"property\",\"required\":true}]}}"

RUN yum groupinstall -y  'Development Tools' \
 && yum install -y python-devel gdal-devel gdal gdal-python python-pip numpy scipy xerces-c \
 && yum clean all \
 && pip install rasterio

WORKDIR /wizards/
ADD centroid.py /wizards/
ADD ace.*wiz /wizards/
ADD oli-vis.wmd /wizards/
ADD runOpticks.sh /wizards/
RUN useradd --uid 1001 scale; chown scale /wizards/*
USER scale
ENTRYPOINT ["./runOpticks.sh"]
