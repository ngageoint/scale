FROM tclarke/opticks
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

LABEL com.ngageoint.scale.job-type="{\"name\":\"tad\",\"version\":\"1.0.0\",\"title\":\"Topological Anomaly Detector\",\"description\":\"Detects spectral anomalies using the tad anomaly detector. Stores result in a PostGIS database.\",\"author_name\":\"Trevor R.H. Clarke \\u003ctclarke@ball.com\\u003e\",\"docker_image\":\"devdocker-reg.devnet.prv:5000/geoint/tad_1.0\",\"priority\":250,\"timeout\":300,\"max_tries\":2,\"cpus_required\":3,\"mem_required\":1024,\"interface\":{\"version\":\"1.0\",\"command\":\"./runOpticks.sh\",\"command_arguments\":\"$ {image} $ {job_output_dir} $ {pg_connect_string}\",\"input_data\":[{\"name\":\"image\",\"type\":\"file\",\"required\":true,\"media_types\":[\"image/tiff\"]},{\"name\":\"pg_connect_string\",\"type\":\"property\",\"required\":true}]}}"

RUN yum groupinstall -y  'Development Tools' \
 && yum install -y python-devel gdal-devel gdal gdal-python python-pip numpy scipy xerces-c \
 && yum clean all \
 && pip install rasterio

WORKDIR /wizards/
ADD centroid.py /wizards/
ADD tad.*wiz /wizards/
ADD runOpticks.sh /wizards/
RUN useradd --uid 1001 scale; chown scale /wizards/*
USER scale
ENTRYPOINT ["./runOpticks.sh"]
