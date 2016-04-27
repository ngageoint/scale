FROM tclarke/opticks
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

ADD ace.*wiz /wizards/
ADD jhu.becknic.manmade.asphalt.paving.solid.0095uuu.spectrum.txt /wizards/
ADD oli-vis.wmd /wizards/
ADD runOpticks.sh ./
RUN useradd --uid 1001 scale; chown scale /wizards/ace.* runOpticks.sh
USER scale
ENTRYPOINT ["./runOpticks.sh"]
