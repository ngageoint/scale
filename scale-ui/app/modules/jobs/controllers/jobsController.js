(function () {
    'use strict';

    angular.module('scaleApp').controller('jobsController', function ($scope, $location, $uibModal, scaleConfig, scaleService, stateService, navService, subnavService, userService, jobService, jobExecutionService, jobTypeService, loadService, gridFactory, toastr) {
        subnavService.setCurrentPath('jobs');

        var vm = this,
            jobTypeViewAll = { name: 'VIEW ALL', title: 'VIEW ALL', version: '', id: 0 };

        vm.jobsParams = stateService.getJobsParams();

        vm.stateService = stateService;
        vm.loading = true;
        vm.readonly = true;
        vm.jobTypeValues = [jobTypeViewAll];
        vm.jobExecution = null;
        vm.selectedJobType = vm.jobsParams.job_type_id ? vm.jobsParams.job_type_id : jobTypeViewAll;
        vm.jobStatusValues = scaleConfig.jobStatus;
        vm.selectedJobStatus = vm.jobsParams.status || vm.jobStatusValues[0];
        vm.errorCategoryValues = _.map(scaleConfig.errorCategories, 'name');
        vm.selectedErrorCategory = vm.jobsParams.error_category || vm.errorCategoryValues[0];
        vm.subnavLinks = scaleConfig.subnavLinks.jobs;
        vm.actionClicked = false;
        vm.lastModifiedStart = moment.utc(vm.jobsParams.started).toDate();
        vm.lastModifiedStartPopup = {
            opened: false
        };
        vm.openLastModifiedStartPopup = function ($event) {
            $event.stopPropagation();
            vm.lastModifiedStartPopup.opened = true;
        };
        vm.lastModifiedStop = moment.utc(vm.jobsParams.ended).toDate();
        vm.lastModifiedStopPopup = {
            opened: false
        };
        vm.openLastModifiedStopPopup = function ($event) {
            $event.stopPropagation();
            vm.lastModifiedStopPopup.opened = true;
        };
        vm.dateModelOptions = {
            timezone: '+000'
        };
        vm.gridOptions = gridFactory.defaultGridOptions();
        vm.gridOptions.paginationCurrentPage = vm.jobsParams.page || 1;
        vm.gridOptions.paginationPageSize = vm.jobsParams.page_size || vm.gridOptions.paginationPageSize;
        vm.gridOptions.data = [];

        var filteredByJobType = vm.jobsParams.job_type_id ? true : false,
            filteredByJobStatus = vm.jobsParams.status ? true : false,
            filteredByErrorCategory = vm.jobsParams.error_category ? true : false,
            filteredByOrder = vm.jobsParams.order ? true : false;

        vm.colDefs = [
            {
                field: 'job_type',
                displayName: 'Job Type',
                cellTemplate: '<div class="ui-grid-cell-contents"><span ng-bind-html="row.entity.job_type.getIcon()"></span> {{ row.entity.job_type.title }} {{ row.entity.job_type.version }}</div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.vm.selectedJobType" ng-options="jobType as (jobType.title + \' \' + jobType.version) for jobType in grid.appScope.vm.jobTypeValues"></select></div>'
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
                cellTemplate: '<div class="ui-grid-cell-contents">' +
                    '<div class="pull-right">' +
                        '<button ng-show="((!grid.appScope.vm.readonly && !row.entity.is_superseded) && (row.entity.status === \'FAILED\' || row.entity.status === \'CANCELED\'))" ng-click="grid.appScope.vm.requeueJobs({ job_ids: [row.entity.id] })" class="btn btn-xs btn-default" title="Requeue Job">' +
                            '<i class="fa fa-repeat"></i></button> ' +
                        '<button ng-show="!grid.appScope.vm.readonly && !row.entity.is_superseded && row.entity.status !== \'COMPLETED\' && row.entity.status !== \'CANCELED\'" ng-click="grid.appScope.vm.cancelJob(row.entity)" class="btn btn-xs btn-default" title="Cancel Job">' +
                            '<i class="fa fa-ban"></i></button>' +
                    '</div> {{ row.entity.status }} <span type="button"  ng-if="row.entity.is_superseded" class="label label-info pull-right" tooltip-append-to-body="true" uib-tooltip="Superseded">S</span></div>',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.vm.selectedJobStatus"><option ng-selected="{{ grid.appScope.vm.jobStatusValues[$index] == grid.appScope.vm.selectedJobStatus }}" value="{{ grid.appScope.vm.jobStatusValues[$index] }}" ng-repeat="status in grid.appScope.vm.jobStatusValues track by $index">{{ status.toUpperCase() }}</option></select></div>'
            },
            {
                field: 'error.category',
                width: 150,
                displayName: 'Error Category',
                filterHeaderTemplate: '<div class="ui-grid-filter-container"><select class="form-control input-sm" ng-model="grid.appScope.vm.selectedErrorCategory"><option ng-selected="{{ grid.appScope.vm.errorCategoryValues[$index] == grid.appScope.vm.selectedErrorCategory }}" value="{{ grid.appScope.vm.errorCategoryValues[$index] }}" ng-repeat="error in grid.appScope.vm.errorCategoryValues track by $index">{{ error.toUpperCase() }}</option></select></div>'
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
                cellTemplate: '<div class="ui-grid-cell-contents text-center"><button ng-click="grid.appScope.vm.showLog(row.entity.id)" class="btn btn-xs btn-default"><i class="fa fa-file-text"></i></button></div>'
            }
        ];

        vm.getJobs = function () {
            jobService.getJobsOnce(vm.jobsParams).then(function (data) {
                vm.gridOptions.totalItems = data.count;
                vm.gridOptions.minRowsToShow = data.results.length;
                vm.gridOptions.virtualizationThreshold = data.results.length;
                vm.gridOptions.data = data.results;
            }).catch(function (error) {
                console.log(error);
            }).finally(function () {
                vm.loading = false;
            });
        };

        vm.getJobTypes = function () {
            jobTypeService.getJobTypesOnce().then(function (data) {
                vm.jobTypeValues.push(data.results);
                vm.jobTypeValues = _.flatten(vm.jobTypeValues);
                vm.selectedJobType = _.find(vm.jobTypeValues, { id: vm.jobsParams.job_type_id }) || jobTypeViewAll;
                vm.getJobs();
            }).catch(function () {
                vm.loading = false;
            });
        };

        vm.showLog = function (jobId) {
            // show log modal
            vm.actionClicked = true;
            jobService.getJobDetail(jobId).then(function (data) {
                vm.jobExecution = data.getLatestExecution();
                jobExecutionService.getJobExecutionDetails(vm.jobExecution.id).then(function(result){
                    vm.jobExecution = result;
                });
                $uibModal.open({
                    animation: true,
                    templateUrl: 'showLog.html',
                    scope: $scope,
                    windowClass: 'log-modal-window'
                });
            });
        };

        vm.requeueJobs = function (jobsParams) {
            if (!jobsParams) {
                jobsParams = vm.jobsParams ? vm.jobsParams : { started: vm.lastModifiedStart.toISOString(), ended: vm.lastModifiedStop.toISOString() };
            }
            vm.actionClicked = true;
            vm.loading = true;
            loadService.requeueJobs(jobsParams).then(function () {
                toastr['success']('Requeue Successful');
                vm.getJobs();
            }).catch(function (error) {
                toastr['error']('Requeue request failed');
                vm.loading = false;
            });
        };

        vm.cancelJob = function (job) {
            vm.actionClicked = true;
            vm.loading = true;
            var originalStatus = job.status;
            job.status = 'CANCEL';
            jobService.updateJob(job.id, { status: 'CANCELED' }).then(function () {
                toastr['success']('Job Canceled');
                job.status = 'CANCELED';
            }).catch(function (error) {
                toastr['error'](error);
                job.status = originalStatus;
            }).finally(function () {
                vm.loading = false;
            });
        };
        
        vm.filterResults = function () {
            stateService.setJobsParams(vm.jobsParams);
            vm.loading = true;
            vm.getJobs();
        };

        vm.updateColDefs = function () {
            vm.gridOptions.columnDefs = gridFactory.applySortConfig(vm.colDefs, vm.jobsParams);
        };

        vm.updateJobOrder = function (sortArr) {
            vm.jobsParams.order = sortArr.length > 0 ? sortArr : null;
            filteredByOrder = sortArr.length > 0;
            vm.filterResults();
        };

        vm.updateJobType = function (value) {
            if (value.id !== vm.jobsParams.job_type_id) {
                vm.jobsParams.page = 1;
            }
            vm.jobsParams.job_type_id = value.id === 0 ? null : value.id;
            vm.jobsParams.page_size = vm.gridOptions.paginationPageSize;
            if (!vm.loading) {
                vm.filterResults();
            }
        };

        vm.updateJobStatus = function (value) {
            if (value != vm.jobsParams.status) {
                vm.jobsParams.page = 1;
            }
            vm.jobsParams.status = value === 'VIEW ALL' ? null : value;
            vm.jobsParams.page_size = vm.gridOptions.paginationPageSize;
            if (!vm.loading) {
                vm.filterResults();
            }
        };

        vm.updateErrorCategory = function (value) {
            if (value != vm.jobsParams.error_category) {
                vm.jobsParams.page = 1;
            }
            vm.jobsParams.error_category = value === 'VIEW ALL' ? null : value;
            vm.jobsParams.page_size = vm.gridOptions.paginationPageSize;
            if (!vm.loading) {
                vm.filterResults();
            }
        };

        vm.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            vm.gridApi = gridApi;
            vm.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                if (vm.actionClicked) {
                    vm.actionClicked = false;
                } else {
                    $location.path('/jobs/job/' + row.entity.id).search('');
                }
            });
            vm.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                vm.jobsParams.page = currentPage;
                vm.jobsParams.page_size = pageSize;
                vm.filterResults();
            });
            vm.gridApi.core.on.sortChanged($scope, function (grid, sortColumns) {
                _.forEach(vm.gridApi.grid.columns, function (col) {
                    col.colDef.sort = col.sort;
                });
                stateService.setJobsColDefs(vm.gridApi.grid.options.columnDefs);
                var sortArr = [];
                _.forEach(sortColumns, function (col) {
                    sortArr.push(col.sort.direction === 'desc' ? '-' + col.field : col.field);
                });
                vm.updateJobOrder(sortArr);
            });
        };

        vm.initialize = function () {
            stateService.setJobsParams(vm.jobsParams);
            vm.updateColDefs();
            var user = userService.getUserCreds();
            vm.readonly = !(user && user.is_admin);
            vm.getJobTypes();
            navService.updateLocation('jobs');
        };

        vm.initialize();

        $scope.$watch('vm.selectedJobType', function (value) {
            if (parseInt(value)) {
                value = _.find(vm.jobTypeValues, {id: parseInt(value)});
            }
            if (value) {
                if (vm.loading) {
                    if (filteredByJobType) {
                        vm.updateJobType(value);
                    }
                } else {
                    filteredByJobType = !angular.equals(value, jobTypeViewAll);
                    vm.updateJobType(value);
                }
            }
        });

        $scope.$watch('vm.selectedJobStatus', function (value) {
            if (vm.loading) {
                if (filteredByJobStatus) {
                    vm.updateJobStatus(value);
                }
            } else {
                filteredByJobStatus = value !== 'VIEW ALL';
                vm.updateJobStatus(value);
            }
        });

        $scope.$watch('vm.selectedErrorCategory', function (value) {
            if (vm.loading) {
                if (filteredByErrorCategory) {
                    vm.updateErrorCategory(value);
                }
            } else {
                filteredByErrorCategory = value !== 'VIEW ALL';
                vm.updateErrorCategory(value);
            }
        });

        $scope.$watch('vm.lastModifiedStart', function (value) {
            if (!vm.loading) {
                vm.jobsParams.started = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watch('vm.lastModifiedStop', function (value) {
            if (!vm.loading) {
                vm.jobsParams.ended = value.toISOString();
                vm.filterResults();
            }
        });

        $scope.$watchCollection('vm.stateService.getJobsColDefs()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.colDefs = newValue;
            vm.updateColDefs();
        });

        $scope.$watchCollection('vm.stateService.getJobsParams()', function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            vm.jobsParams = newValue;
            vm.updateColDefs();
        });
    });
})();
