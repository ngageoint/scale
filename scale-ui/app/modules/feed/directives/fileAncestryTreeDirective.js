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

        function getNodeHtml(file) {
            var iconHtml = scaleService.getMediaTypeHtml(file.media_type);
            var html = "<div class='graph'>";
            html += "<span class='name'><a ng-show='" + file.url + "' href='" + file.url + "' target='_jobfile'>" + iconHtml + ' ' + file.file_name + "</a></span>";
            html += "</div>";

            return html;
        };

        function getJobNodeHtml(jobtype, jobid){
            var html = "<div>";
            html += "<span class='status'></span><span class='job-name'>" + jobtype.name + ":" + jobid + "</span>";
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
                    padding: 10
                    //width: 150,
                    //height: 50
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
                        padding: 10
                        //width: 150,
                        //height: 50
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
                        padding: 10
                        //width: 150,
                        //height: 50
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
                var vbxheight = vbx[2]*ratio;
                svg.attr('viewBox', vbx[0] + ' ' + vbx[1] + ' ' + vbx[2] + ' ' + vbxheight);

                var initialScale = vbx[2]/gwidth;

                zoom
                    .translate([0, 0])
                    .scale(initialScale)
                    .event(svg);


                // set appropriate class for job nodes
                $('.job-name').closest('.node').children('rect').attr('class', 'job'); //.addClass('job');

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
