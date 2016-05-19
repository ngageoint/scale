(function () {
    'use strict';

    angular.module('scaleApp').controller('jobsController', function($rootScope, $scope, $location, $uibModal, navService, jobService, jobTypeService, jobExecutionService, uiGridConstants, scaleConfig, subnavService, gridFactory, loadService, scaleService, userService, moment, toastr) {
        var self = this;

        self.jobsParams = {
            page: null, page_size: null, started: null, ended: null, order: $rootScope.jobsControllerOrder || '-last_modified', status: null, error_category: null, job_type_id: null, job_type_name: null, job_type_category: null, url: null
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
            filteredByErrorCategory = self.jobsParams.error_category ? true : false,
            filteredByOrder = self.jobsParams.order ? true : false;

        $scope.jobsData = {};
        $scope.loading = true;
        $scope.jobTypeValues = [];
        $scope.jobExecution = null;
        $scope.selectedJobType = self.jobsParams.job_type_id || 0;
        $scope.jobStatusValues = scaleConfig.jobStatus;
        $scope.selectedJobStatus = self.jobsParams.status || $scope.jobStatusValues[0];
        $scope.errorCategoryValues = scaleConfig.errorCategories;
        $scope.selectedErrorCategory = self.jobsParams.error_category || $scope.errorCategoryValues[0];
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        $scope.actionClicked = false;
        $scope.gridStyle = '';
        $scope.readonly = true;
        $scope.lastModifiedStart = self.jobsParams.started ? moment.utc(self.jobsParams.started).toDate() : moment.utc().subtract(1, 'weeks').startOf('d').toDate();
        $scope.lastModifiedStartPopup = {
            opened: false
        };
        $scope.openLastModifiedStartPopup = function ($event) {
            $event.stopPropagation();
            $scope.lastModifiedStartPopup.opened = true;
        };
        $scope.lastModifiedStop = self.jobsParams.ended ? moment.utc(self.jobsParams.ended).toDate() : moment.utc().endOf('d').toDate();
        $scope.lastModifiedStopPopup = {
            opened: false
        };
        $scope.openLastModifiedStopPopup = function ($event) {
            $event.stopPropagation();
            $scope.lastModifiedStopPopup.opened = true;
        };
        $scope.dateModelOptions = {
            timezone: '+000'
        };

        subnavService.setCurrentPath('jobs');

        var defaultColumnDefs = [
            {
                field: 'job_type',
                displayName: 'Job Type',
                cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.job_type.getIcon()"></span> {{ row.entity.job_type.title }} {{ row.entity.job_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedJobType"><option ng-if="grid.appScope.jobTypeValues[$index]" ng-selected="{{ grid.appScope.jobTypeValues[$index].id == grid.appScope.selectedJobType }}" value="{{ grid.appScope.jobTypeValues[$index].id }}" ng-repeat="jobType in grid.appScope.jobTypeValues track by $index">{{ grid.appScope.jobTypeValues[$index].title }} {{ grid.appScope.jobTypeValues[$index].version }}</option></select></div>'
            },
            {
                field: 'created',
                displayName: 'Created (Z)',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.created_formatted }}</div>'
            },
            {
                field: 'last_modified',
                displayName: 'Last Modified (Z)',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.last_modified_formatted }}</div>'
            },
            {
                field: 'duration',
                enableFiltering: false,
                enableSorting: false,
                width: 120,
                cellTemplate: '<div class="ui-grid-cell-contents text-right">{{ row.entity.getDuration() }}</div>'
            },
            {
                field: 'status',
                width: 150,
                cellTemplate: '<div class="ui-grid-cell-contents"><div class="pull-right"><button ng-show="((!grid.appScope.readonly) && (row.entity.status === \'FAILED\' || row.entity.status === \'CANCELED\'))" ng-click="grid.appScope.requeueJobs({ job_ids: [row.entity.id] })" class="btn btn-xs btn-default" title="Requeue Job"><i class="fa fa-repeat"></i></button> <button ng-show="!grid.appScope.readonly && row.entity.status !== \'COMPLETED\' && row.entity.status !== \'CANCELED\'" ng-click="grid.appScope.cancelJob(row.entity)" class="btn btn-xs btn-default" title="Cancel Job"><i class="fa fa-ban"></i></button></div> {{ row.entity.status }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedJobStatus"><option ng-selected="{{ grid.appScope.jobStatusValues[$index] == grid.appScope.selectedJobStatus }}" value="{{ grid.appScope.jobStatusValues[$index] }}" ng-repeat="status in grid.appScope.jobStatusValues track by $index">{{ status.toUpperCase() }}</option></select></div>'
            },
            {
                field: 'error.category',
                width: 150,
                displayName: 'Error Category',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedErrorCategory"><option ng-selected="{{ grid.appScope.errorCategoryValues[$index] == grid.appScope.selectedErrorCategory }}" value="{{ grid.appScope.errorCategoryValues[$index] }}" ng-repeat="error in grid.appScope.errorCategoryValues track by $index">{{ error.toUpperCase() }}</option></select></div>'
            },
            {
                field: 'error.title',
                displayName: 'Error',
                cellTemplate: '<div class="ui-grid-cell-contents"><div uib-tooltip="{{ row.entity.error.description }}" tooltip-append-to-body="true">{{ row.entity.error.title }}</div></div>',
                width: 200,
                enableFiltering: false
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
            value = parseInt(value);
            if (value !== self.jobsParams.job_type_id) {
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

        self.updateErrorCategory = function (value) {
            if (value != self.jobsParams.error_category) {
                self.jobsParams.page = 1;
            }
            self.jobsParams.error_category = value === 'VIEW ALL' ? null : value;
            self.jobsParams.page_size = $scope.gridOptions.paginationPageSize;
            console.log('selectedErrorCategory');
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

        $scope.$watch('selectedErrorCategory', function (value) {
            if ($scope.loading) {
                if (filteredByErrorCategory) {
                    self.updateErrorCategory(value);
                }
            } else {
                filteredByErrorCategory = value !== 'VIEW ALL';
                self.updateErrorCategory(value);
            }
        });

        self.updateJobOrder = function (sortArr) {
            self.jobsParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            $scope.filterResults();
        };

        $scope.$watch('lastModifiedStart', function (value) {
            if (!$scope.loading) {
                self.jobsParams.started = value.toISOString();
                $scope.filterResults();
            }
        });

        $scope.$watch('lastModifiedStop', function (value) {
            if (!$scope.loading) {
                self.jobsParams.ended = value.toISOString();
                $scope.filterResults();
            }
        });

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
                var modalInstance = $uibModal.open({
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
            $scope.loading = true;
            self.getJobs();
        };

        $scope.requeueJobs = function (jobsParams) {
            if (!jobsParams) {
                jobsParams = self.jobsParams ? self.jobsParams : { started: $scope.lastModifiedStart.toISOString(), ended: $scope.lastModifiedStop.toISOString() };
            }
            $scope.actionClicked = true;
            $scope.loading = true;
            loadService.requeueJobs(jobsParams).then(function () {
                toastr['success']('Requeue Successful');
                self.getJobs();
            }).catch(function (error) {
                toastr['error']('Requeue request failed');
                console.log(error);
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
                if (!self.jobsParams.started) {
                    self.jobsParams.started = moment.utc($scope.lastModifiedStart).toISOString();
                    $location.search('started', self.jobsParams.started).replace();
                }
                if (!self.jobsParams.ended) {
                    self.jobsParams.ended = moment.utc($scope.lastModifiedStop).toISOString();
                    $location.search('ended', self.jobsParams.ended).replace();
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
                offset = scaleConfig.headerOffset + scaleConfig.dateFilterOffset,
                gridMaxHeight = viewport.height - offset;

            $scope.gridStyle = 'height: ' + gridMaxHeight + 'px; max-height: ' + gridMaxHeight + 'px; overflow-y: auto;';
        });
    });
})();
