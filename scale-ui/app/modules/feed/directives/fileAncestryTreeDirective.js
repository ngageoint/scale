/**
 * <scale-file-ancestry-tree />
 */
(function () {
    angular.module('scaleApp').controller('scaleFileAncestryTreeController', function ($scope, scaleService) {
        var vm = this;
        vm.source = $scope.source;

        $scope.$watchCollection('vm.source', function() {
            draw();
            //console.log(vm.source);
        });

        function formatFileName(filename){
            var maxlen = 25;
            var newfname = filename;
            if(filename.length > 30){
                var ext = filename.substring(filename.lastIndexOf('.')+1);
                var firstpart = filename.substring(0, filename.lastIndexOf('.'));
                var firstpartLen = maxlen - ext.length;
                var newfname = filename.substring(0,firstpartLen-1) + '...' + ext;
            }
            return newfname;
        };

        function getNodeHtml(file) {
            var iconHtml = scaleService.getMediaTypeHtml(file.media_type);
            var fname = formatFileName(file.file_name);
            var html = "<div class='graph'>";
            html += "<span class='name' title='" + file.file_name + "'>";
            html += "<a ng-show='" + file.url + "' href='" + file.url + "' target='_jobfile'>" + iconHtml + " " + fname + "</a>";
            html += "</span>";
            html += "</div>";

            return html;
        };

        function getJobNodeHtml(jobtype, jobid){
            var html = "<div>";
            html += "<span class='status'></span><span class='job-name'><a href='#/jobs/job/" + jobid + "'>" + jobtype.name + "</a></span>";
            html += "</div>";

            return html;
        }

        function draw() {
            if(vm.source && vm.source !== undefined){
                var svg = d3.select("svg");
                var inner = svg.select("g");

                // Set up zoom support
                var zoom = d3.behavior.zoom()
                    .on("zoom", function() {
                        // don't zoom on WheelEvent or MouseEvent, just window sizing
                        console.log('zoomed');
                        if(d3.event.sourceEvent === null){
                            inner.attr("transform", "translate(" + d3.event.translate + ")" +
                                "scale(" + d3.event.scale + ")");
                        }
                });
                svg.call(zoom);

                var render = new dagreD3.render();
                // Left-to-right layout
                var g = new dagreD3.graphlib.Graph({multigraph: true});
                g.setGraph({
                    nodesep: 30,
                    ranksep: 70,
                    rankdir: "LR",
                    marginx: 20,
                    marginy: 0
                });

                //Starting node
                var html = getNodeHtml(vm.source);
                g.setNode('file-' + vm.source.id, {
                    labelType: "html",
                    label: html,
                    rx: 10,
                    ry: 10,
                    padding: 10,
                    width: 250,
                    height: 20
                });

                // Products
                for (var id in vm.source.products) {
                    var prod = vm.source.products[id];
                    var jobNodeHtml = getJobNodeHtml(prod.job_type, prod.job.id);
                    // Add node for the job
                    g.setNode('job-' + prod.job.id, {
                        labelType: "html",
                        label: jobNodeHtml,
                        rx: 10,
                        ry: 10,
                        padding: 10,
                        width: 200,
                        height: 20
                    });
                    g.setEdge('file-'+vm.source.id, 'job-'+prod.job.id, {
                        //labelType: "html",
                        //label: "<a href='#/jobs/job/" + prod.job.id + "'>" + prod.job_type.name + "</a>"
                        //width: 40
                    });


                    var html = getNodeHtml(prod);
                    g.setNode('file-' + prod.id, {
                        labelType: "html",
                        label: html,
                        rx: 10,
                        ry: 10,
                        padding: 10,
                        width: 250,
                        height: 20
                    });
                    g.setEdge('job-'+prod.job.id, 'file-'+prod.id, {
                        //labelType: "html",
                        //label: "<a href='#/jobs/job/" + prod.job.id + "'>" + prod.job_type.name + "</a>"
                        //width: 40
                    });

                }

                var render = new dagreD3.render();

                // Run the renderer. This is what draws the final graph.
                render(inner, g);

                // Center the graph
                var vbx = svg.attr('viewBox').split(' ');
                var gwidth = g.graph().width;
                var gheight = g.graph().height;
                var ratio = gheight/gwidth;

                console.log(gheight);
                console.log(vbx[3]);

                // If graph is shorter than container, shrink the container height
                if( gheight < vbx[3] ){
                    svg.attr('viewBox', vbx[0] + ' ' + vbx[1] + ' ' + vbx[2] + ' ' + gheight*1.1);
                }

                // Scale graph based on width or height based on which exceeds
                // viewbox by most pixels
                var initialScale = Math.min((vbx[2]*0.95)/gwidth,(vbx[3]*0.95)/gheight);
                zoom
                    .translate([(vbx[2]*0.02), (vbx[3]*0.02)])
                    .scale(initialScale)
                    .event(svg);

                // set appropriate class for job nodes
                $('.job-name').closest('.node').children('rect').attr('class', 'job'); //.addClass('job');

                // clear zoom handler and mousewheel events
                // so they don't interfere with scrolling
                zoom.on('zoom', null);
                svg.on("mousedown.zoom", null)
                    .on("mousewheel.zoom", null)
                    .on("mousemove.zoom", null)
                    .on("DOMMouseScroll.zoom", null)
                    .on("dblclick.zoom", null)
                    .on("touchstart.zoom", null)
                    .on("touchmove.zoom", null)
                    .on("touchend.zoom", null)
                    .on("wheel.zoom", null);
            }

        }



    }).directive('scaleFileAncestryTree', function () {
        'use strict';
        /**
         * Usage: <scale-file-ancestry-tree source="source" />
         */
        return {
            controller: 'scaleFileAncestryTreeController',
            templateUrl: 'modules/feed/directives/fileAncestryTreeTemplate.html',
            restrict: 'E',
            scope: {
                source: '='
            }
        };

    });
})();
