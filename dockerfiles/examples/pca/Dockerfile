FROM tclarke/opticks
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

ADD pca.*wiz /wizards/
ADD runOpticks.sh ./
RUN useradd --uid 1001 scale; chown scale /wizards/pca.* runOpticks.sh
USER scale
ENTRYPOINT ["./runOpticks.sh"]
