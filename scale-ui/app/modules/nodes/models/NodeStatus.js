(function() {
    'use strict';

    angular.module('scaleApp').factory('NodeStatus', function (scaleConfig, nodeUpdateService, Node, JobExecution) {
        var NodeStatus = function (node, is_online, job_exe_counts, job_exes_running) {
            this.node = Node.transformer(node);
            this.is_online = is_online;
            this.job_exe_counts = job_exe_counts;
            this.job_exes_running = JobExecution.transformer(job_exes_running);
        };

        //public methods
        NodeStatus.prototype = {
            toString: function () {
                return 'NodeStatus';
            },
            getCompleted: function () {
                var completed = _.find(this.job_exe_counts, 'status', 'COMPLETED');
                return completed ? completed.count : 0;
            },
            getFailed: function () {
                var failed = _.find(this.job_exe_counts, 'status', 'FAILED');
                return failed ? failed.count : 0;
            },
            getCellFill: function () {
                var color = '';
                if (this.is_online) {
                    if (this.node.is_paused_errors) {
                        color = scaleConfig.colors.chart_orange;
                    } else if (this.node.is_paused) {
                        color = scaleConfig.colors.chart_yellow;
                    } else {
                        color = scaleConfig.colors.chart_green;
                    }
                } else {
                    color = scaleConfig.colors.chart_red;
                }
                return color;
            },
            getCellActivity: function () {
                return '';
            },
            getCellError: function () {
                return 'Failed: ' + this.getFailed();
            },
            getCellTotal: function () {
                return 'Completed: ' + this.getCompleted();
            },
            getCellStatus: function () {
                if (this.is_online) {
                    if (this.node.is_paused_errors) {
                        return 'High Failure Rate';
                    } else if (this.node.is_paused) {
                        return 'Paused';
                    } else {
                        return 'Online';
                    }
                } else {
                    return 'Offline';
                }
            },
            getCellJobs: function () {
                var text = '';
                _.forEach(this.job_exes_running, function (jobExecution) {
                    text = jobExecution.job.job_type.icon_code ?
                    text + ' ' + '&#x' + jobExecution.job.job_type.icon_code + ';' :
                    text + ' ' + '&#x' + scaleConfig.defaultIconCode + ';';
                });
                return text;
            },
            getCellPauseResume: function () {
                return this.node.is_paused ? '&#xf04b;' : '&#xf04c;';
            },
            pauseResumeCell: function (pause_reason) {
                var updateData = {
                    hostname: this.node.hostname,
                    port: this.node.port,
                    pause_reason: pause_reason || '',
                    is_paused: !this.node.is_paused
                };
                return nodeUpdateService.updateNode(this.node.id, updateData).then(function (result) {
                    return Node.transformer(result);
                }).catch(function (error) {
                    console.log(error);
                });
            }
        };

        // static methods, assigned to class
        NodeStatus.build = function (data) {
            if (data) {
                return new NodeStatus(
                    data.node,
                    data.is_online,
                    data.job_exe_counts,
                    data.job_exes_running
                );
            }
            return new NodeStatus();
        };

        NodeStatus.transformer = function (data) {
            if (angular.isArray(data)) {
                return data
                    .map(NodeStatus.build);
            }
            return NodeStatus.build(data);
        };

        return NodeStatus;
    });
})();
