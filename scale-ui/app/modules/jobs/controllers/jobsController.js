(function () {
    'use strict';

    angular.module('scaleApp').controller('jobsController', function($rootScope, $scope, $location, $modal, navService, jobService, jobTypeService, jobExecutionService, uiGridConstants, scaleConfig, subnavService, gridFactory, loadService, scaleService, userService) {
        var self = this;

        self.jobsParams = {
            page: null, page_size: null, started: null, ended: null, order: $rootScope.jobsControllerOrder || '-last_modified', status: null, job_type_id: null, job_type_name: null, job_type_category: null, url: null
        };

        // check for jobsParams in query string, and update as necessary
        _.forEach(_.pairs(self.jobsParams), function (param) {
            var value = _.at($location.search(), param[0]);
            if (value.length > 0) {
                self.jobsParams[param[0]] = value.length > 1 ? value : value[0];
            }
        });

        var gridPageNumber = self.jobsParams.page || 1,
            filteredByJobType = self.jobsParams.job_type_id ? true : false,
            filteredByJobStatus = self.jobsParams.status ? true : false,
            filteredByOrder = self.jobsParams.order ? true : false;

        $scope.jobsData = {};
        $scope.loading = true;
        $scope.jobTypeValues = [];
        $scope.jobExecution = null;
        $scope.selectedJobType = self.jobsParams.job_type_id || 0;
        $scope.jobStatusValues = scaleConfig.jobStatus;
        $scope.selectedJobStatus = self.jobsParams.status || $scope.jobStatusValues[0];
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        $scope.actionClicked = false;
        $scope.gridStyle = '';
        $scope.readonly = true;

        subnavService.setCurrentPath('jobs');

        var defaultColumnDefs = [
            {
                field: 'job_type',
                displayName: 'Job Type',
                cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.job_type.getIcon()"></span> {{ row.entity.job_type.title }} {{ row.entity.job_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedJobType"><option ng-if="grid.appScope.jobTypeValues[$index]" ng-selected="{{ grid.appScope.jobTypeValues[$index].id == grid.appScope.selectedJobType }}" value="{{ grid.appScope.jobTypeValues[$index].id }}" ng-repeat="jobType in grid.appScope.jobTypeValues track by $index">{{ grid.appScope.jobTypeValues[$index].title }} {{ grid.appScope.jobTypeValues[$index].version }}</option></select>'
            },
            {
                field: 'created',
                displayName: 'Created',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.created_formatted }}</div>'
            },
            {
                field: 'last_modified',
                displayName: 'Last Modified',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.last_modified_formatted }}</div>'
                //cellFilter: 'date:\'' + scaleConfig.dateFormats.day_minute_utc + '\'',
            },
            { field: 'duration', enableFiltering: false, enableSorting: false, cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.getDuration() }}</div>' },
            {
                field: 'status',
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.status }} <button ng-show="((!grid.appScope.readonly) && (row.entity.status === \'FAILED\' || row.entity.status === \'CANCELED\'))" ng-click="grid.appScope.requeueJob(row.entity)" class="btn btn-xs btn-default" title="Requeue Job"><i class="fa fa-repeat"></i></button> <button ng-show="!grid.appScope.readonly && row.entity.status !== \'COMPLETED\' && row.entity.status !== \'CANCELED\'" ng-click="grid.appScope.cancelJob(row.entity)" class="btn btn-xs btn-default" title="Cancel Job"><i class="fa fa-ban"></i></button></div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedJobStatus"><option ng-selected="{{ grid.appScope.jobStatusValues[$index] == grid.appScope.selectedJobStatus }}" value="{{ grid.appScope.jobStatusValues[$index] }}" ng-repeat="status in grid.appScope.jobStatusValues track by $index">{{ status.toUpperCase() }}</option></select></div>'
            },
            {
                field: 'id',
                displayName: 'Log',
                enableFiltering: false,
                sortable: false,
                width: 60,
                cellTemplate: '<div class="ui-grid-cell-contents text-center"><button ng-click="grid.appScope.showLog(row.entity.id)" class="btn btn-xs btn-default"><i class="fa fa-file-text"></i></button></div>'
            }
        ];

        $scope.gridOptions = gridFactory.defaultGridOptions();
        $scope.gridOptions.paginationCurrentPage = parseInt(self.jobsParams.page || 1);
        $scope.gridOptions.paginationPageSize = parseInt(self.jobsParams.page_size) || $scope.gridOptions.paginationPageSize;
        var colDefs = $rootScope.colDefs ? $rootScope.colDefs : defaultColumnDefs;
        $scope.gridOptions.columnDefs = gridFactory.applySortConfig(colDefs, self.jobsParams);
        $scope.gridOptions.data = [];
        $scope.gridOptions.onRegisterApi = function (gridApi) {
                //set gridApi on scope
                $scope.gridApi = gridApi;
                $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                    if ($scope.actionClicked) {
                        $scope.actionClicked = false;
                    } else {
                        $scope.$apply(function(){
                            $location.path('/jobs/job/' + row.entity.id);
                        });
                    }

                });
                $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                    self.jobsParams.page = currentPage;
                    self.jobsParams.page_size = pageSize;
                    console.log('gridApi');
                    $scope.filterResults();
                });
                $scope.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                    $rootScope.colDefs = null;
                    _.forEach($scope.gridApi.grid.columns, function (col) {
                        col.colDef.sort = col.sort;
                    });
                    $rootScope.colDefs = $scope.gridApi.grid.options.columnDefs;
                    var sortArr = [];
                    _.forEach(sortColumns, function (col) {
                        sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                    });
                    self.updateJobOrder(sortArr);
                });
            };


        $scope.showStatus = function (status) {
            return _.includes($scope.jobStatusValues, status);
        };

        self.updateJobType = function (value) {
            if (value != self.jobsParams.job_type_id) {
                self.jobsParams.page = 1;
            }
            self.jobsParams.job_type_id = value == 0 ? null : value;
            self.jobsParams.page_size = $scope.gridOptions.paginationPageSize;
            console.log('selectedJobType');
            if (!$scope.loading) {
                $scope.filterResults();
            }
        };

        $scope.$watch('selectedJobType', function (value) {
            if ($scope.loading) {
                if (filteredByJobType) {
                    self.updateJobType(value);
                }
            } else {
                filteredByJobType = value != 0;
                self.updateJobType(value);
            }
        });

        self.updateJobStatus = function (value) {
            if (value != self.jobsParams.status) {
                self.jobsParams.page = 1;
            }
            self.jobsParams.status = value === 'VIEW ALL' ? null : value;
            self.jobsParams.page_size = $scope.gridOptions.paginationPageSize;
            console.log('selectedJobStatus');
            if (!$scope.loading) {
                $scope.filterResults();
            }
        };

        $scope.$watch('selectedJobStatus', function (value) {
            if ($scope.loading) {
                if (filteredByJobStatus) {
                    self.updateJobStatus(value);
                }
            } else {
                filteredByJobStatus = value !== 'VIEW ALL';
                self.updateJobStatus(value);
            }
        });

        self.updateJobOrder = function (sortArr) {
            self.jobsParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            $scope.filterResults();
        };

        /*$scope.$watch('gridApi', function (gridApi) {
            if (filteredByOrder) {
                gridApi.core.raise.sortChanged();
            }
        });*/

        $scope.showLog = function (jobId) {
            // show log modal
            $scope.actionClicked = true;
            console.log('show log modal');
            jobService.getJobDetail(jobId).then(function (data) {
                $scope.selectedJob = data.job_type.title + ' ' + data.job_type.version;
                $scope.jobExecution = data.getLatestExecution();
                var modalInstance = $modal.open({
                    animation: true,
                    templateUrl: 'showLog.html',
                    scope: $scope,
                    size: 'lg',
                    windowClass: 'log-modal-window'
                });
            });
        };

        $scope.filterResults = function () {
            _.forEach(_.pairs(self.jobsParams), function (param) {
                $location.search(param[0], param[1]);
            });
            self.getJobs();
        };

        $scope.requeueJob = function (job) {
            $scope.actionClicked = true;
            $scope.loading = true;
            var originalStatus = job.status;
            loadService.requeueJob(job.id).then(function (data) {
                toastr['success']('Requeued Job');
                job.status = data.status;
            }).catch(function (error) {
                toastr['error'](error);
                console.log(error);
                job.status = originalStatus;
            }).finally(function () {
                $scope.loading = false;
            });
        };

        $scope.cancelJob = function (job) {
            $scope.actionClicked = true;
            $scope.loading = true;
            var originalStatus = job.status;
            job.status = 'CANCEL';
            jobService.updateJob(job.id, { status: 'CANCELED' }).then(function (data) {
                toastr['success']('Job Canceled');
                job.status = 'CANCELED';
            }).catch(function (error) {
                toastr['error'](error);
                console.log(error);
                job.status = originalStatus;
            }).finally(function () {
                $scope.loading = false;
            });
        };

        self.getJobs = function () {
            jobService.getJobsOnce(self.jobsParams).then(function (data) {
                $scope.jobsData = data.results;
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.data = data.results;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        self.getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                $scope.jobTypeValues = data.results;
                $scope.jobTypeValues.unshift({ name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 });
                /*if (!filteredByJobType && !filteredByJobStatus && !filteredByOrder) {
                    self.getJobs();
                } else {
                    if (filteredByOrder) {
                        self.updateJobOrder(self.jobsParams.order);
                    }
                }*/
                self.getJobs(self.jobsParams);
            }).catch(function (error) {
                $scope.loading = false;
                console.log(error);
            });
        };

        self.initialize = function () {
            if (typeof $rootScope.colDefs === 'undefined') {
                // root column defs have not been altered by user, so set up defaults
                if (!self.jobsParams.order) {
                    self.jobsParams.order = '-last_modified';
                    $location.search('order', self.jobsParams.order).replace();
                }
                if (!self.jobsParams.page_size) {
                    self.jobsParams.page_size = $scope.gridOptions.paginationPageSize;
                    $location.search('page_size', self.jobsParams.page_size).replace();
                }
            }
            self.getJobTypes();
            $rootScope.user = userService.getUserCreds();

            if ($rootScope.user) {
                $scope.readonly = false;
            }
            navService.updateLocation('jobs');
        };

        self.initialize();

        angular.element(document).ready(function () {
            // set container heights equal to available page height
            var viewport = scaleService.getViewportSize(),
                offset = scaleConfig.headerOffset,
                gridMaxHeight = viewport.height - offset;

            $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px; overflow-y: auto;';
        });
    });
})();
