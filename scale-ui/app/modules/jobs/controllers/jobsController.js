(function () {
    'use strict';

    angular.module('scaleApp').controller('jobsController', function ($scope, $location, $uibModal, scaleConfig, scaleService, stateService, navService, subnavService, userService, jobService, jobTypeService, loadService, gridFactory, toastr) {
        subnavService.setCurrentPath('jobs');

        var self = this,
            jobTypeViewAll = { name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 };

        self.jobsParams = stateService.getJobsParams();

        $scope.stateService = stateService;
        $scope.loading = true;
        $scope.readonly = true;
        $scope.jobTypeValues = [jobTypeViewAll];
        $scope.jobExecution = null;
        $scope.selectedJobType = self.jobsParams.job_type_id ? self.jobsParams.job_type_id : jobTypeViewAll;
        $scope.jobStatusValues = scaleConfig.jobStatus;
        $scope.selectedJobStatus = self.jobsParams.status || $scope.jobStatusValues[0];
        $scope.errorCategoryValues = _.map(scaleConfig.errorCategories, 'name');
        $scope.selectedErrorCategory = self.jobsParams.error_category || $scope.errorCategoryValues[0];
        $scope.subnavLinks = scaleConfig.subnavLinks.jobs;
        $scope.actionClicked = false;
        $scope.lastModifiedStart = moment.utc(self.jobsParams.started).toDate();
        $scope.lastModifiedStartPopup = {
            opened: false
        };
        $scope.openLastModifiedStartPopup = function ($event) {
            $event.stopPropagation();
            $scope.lastModifiedStartPopup.opened = true;
        };
        $scope.lastModifiedStop = moment.utc(self.jobsParams.ended).toDate();
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
        $scope.gridOptions = gridFactory.defaultGridOptions();
        $scope.gridOptions.paginationCurrentPage = self.jobsParams.page || 1;
        $scope.gridOptions.paginationPageSize = self.jobsParams.page_size || $scope.gridOptions.paginationPageSize;
        $scope.gridOptions.data = [];

        var filteredByJobType = self.jobsParams.job_type_id ? true : false,
            filteredByJobStatus = self.jobsParams.status ? true : false,
            filteredByErrorCategory = self.jobsParams.error_category ? true : false,
            filteredByOrder = self.jobsParams.order ? true : false;

        self.colDefs = [
            {
                field: 'job_type',
                displayName: 'Job Type',
                cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.job_type.getIcon()"></span> {{ row.entity.job_type.title }} {{ row.entity.job_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.selectedJobType" ng-options="jobType as (jobType.title + \' \' + jobType.version) for jobType in grid.appScope.jobTypeValues"></select></div>'
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

        self.getJobs = function () {
            jobService.getJobsOnce(self.jobsParams).then(function (data) {
                $scope.gridOptions.totalItems = data.count;
                $scope.gridOptions.minRowsToShow = data.results.length;
                $scope.gridOptions.virtualizationThreshold = data.results.length;
                $scope.gridOptions.data = data.results;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                $scope.loading = false;
            });
        };

        self.getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                $scope.jobTypeValues.push(data.results);
                $scope.jobTypeValues = _.flatten($scope.jobTypeValues);
                $scope.selectedJobType = _.find($scope.jobTypeValues, { id: self.jobsParams.job_type_id }) || jobTypeViewAll;
                self.getJobs();
            }).catch(function () {
                $scope.loading = false;
            });
        };

        $scope.showLog = function (jobId) {
            // show log modal
            $scope.actionClicked = true;
            jobService.getJobDetail(jobId).then(function (data) {
                $scope.jobExecution = data.getLatestExecution();
                $uibModal.open({
                    animation: true,
                    templateUrl: 'showLog.html',
                    scope: $scope,
                    size: 'lg',
                    windowClass: 'log-modal-window'
                });
            });
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
                $scope.loading = false;
            });
        };

        $scope.cancelJob = function (job) {
            $scope.actionClicked = true;
            $scope.loading = true;
            var originalStatus = job.status;
            job.status = 'CANCEL';
            jobService.updateJob(job.id, { status: 'CANCELED' }).then(function () {
                toastr['success']('Job Canceled');
                job.status = 'CANCELED';
            }).catch(function (error) {
                toastr['error'](error);
                job.status = originalStatus;
            }).finally(function () {
                $scope.loading = false;
            });
        };
        
        self.filterResults = function () {
            stateService.setJobsParams(self.jobsParams);
            $scope.loading = true;
            self.getJobs();
        };

        self.updateColDefs = function () {
            $scope.gridOptions.columnDefs = gridFactory.applySortConfig(self.colDefs, self.jobsParams);
        };

        self.updateJobOrder = function (sortArr) {
            self.jobsParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            self.filterResults();
        };

        self.updateJobType = function (value) {
            if (value.id !== self.jobsParams.job_type_id) {
                self.jobsParams.page = 1;
            }
            self.jobsParams.job_type_id = value.id === 0 ? null : value.id;
            self.jobsParams.page_size = $scope.gridOptions.paginationPageSize;
            if (!$scope.loading) {
                self.filterResults();
            }
        };

        self.updateJobStatus = function (value) {
            if (value != self.jobsParams.status) {
                self.jobsParams.page = 1;
            }
            self.jobsParams.status = value === 'VIEW ALL' ? null : value;
            self.jobsParams.page_size = $scope.gridOptions.paginationPageSize;
            if (!$scope.loading) {
                self.filterResults();
            }
        };

        self.updateErrorCategory = function (value) {
            if (value != self.jobsParams.error_category) {
                self.jobsParams.page = 1;
            }
            self.jobsParams.error_category = value === 'VIEW ALL' ? null : value;
            self.jobsParams.page_size = $scope.gridOptions.paginationPageSize;
            if (!$scope.loading) {
                self.filterResults();
            }
        };

        $scope.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            $scope.gridApi = gridApi;
            $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                if ($scope.actionClicked) {
                    $scope.actionClicked = false;
                } else {
                    $scope.$apply(function () {
                        $location.path('/jobs/job/' + row.entity.id);
                    });
                }
            });
            $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                self.jobsParams.page = currentPage;
                self.jobsParams.page_size = pageSize;
                self.filterResults();
            });
            $scope.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                _.forEach($scope.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                stateService.setJobsColDefs($scope.gridApi.grid.options.columnDefs);
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                self.updateJobOrder(sortArr);
            });
        };

        self.initialize = function () {
            $scope.gridStyle = scaleService.setGridHeight(scaleConfig.headerOffset + scaleConfig.dateFilterOffset + scaleConfig.paginationOffset);
            stateService.setJobsParams(self.jobsParams);
            self.updateColDefs();
            var user = userService.getUserCreds();
            $scope.readonly = !(user && user.is_admin);
            self.getJobTypes();
            navService.updateLocation('jobs');
        };

        self.initialize();

        $scope.$watch('selectedJobType', function (value) {
            if (parseInt(value)) {
                value = _.find($scope.jobTypeValues, {id: parseInt(value)});
            }
            if (value) {
                if ($scope.loading) {
                    if (filteredByJobType) {
                        self.updateJobType(value);
                    }
                } else {
                    filteredByJobType = !angular.equals(value, jobTypeViewAll);
                    self.updateJobType(value);
                }
            }
        });

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

        $scope.$watch('lastModifiedStart', function (value) {
            if (!$scope.loading) {
                self.jobsParams.started = value.toISOString();
                self.filterResults();
            }
        });

        $scope.$watch('lastModifiedStop', function (value) {
            if (!$scope.loading) {
                self.jobsParams.ended = value.toISOString();
                self.filterResults();
            }
        });

        $scope.$watchCollection('stateService.getJobsColDefs()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            self.colDefs = newValue;
            self.updateColDefs();
        });

        $scope.$watchCollection('stateService.getJobsParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            self.jobsParams = newValue;
            self.updateColDefs();
        });
    });
})();