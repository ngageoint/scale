FROM tclarke/opticks
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

LABEL com.ngageoint.scale.job-type=""

ADD ace.*wiz /wizards/
ADD oli-vis.wmd /wizards/
ADD runOpticks.sh ./
RUN useradd --uid 1001 scale; chown scale /wizards/ace.* runOpticks.sh
USER scale
ENTRYPOINT ["./runOpticks.sh"]
