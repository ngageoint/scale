(function () {
    'use strict';

    angular.module('scaleApp').controller('workspacesController', function($rootScope, $scope, $location, $uibModal, navService, workspacesService, scaleService, userService, gridFactory, moment, toastr) {
        var self = this;
        $scope.workspaces = [];
        $scope.addBtnClass = 'btn-primary';
        $scope.addBtnIcon = 'fa-plus-circle';
        $scope.masterClass = 'col-xs-3';
        $scope.detailClass = 'col-xs-9';
        $scope.mode = "view";
        $scope.readonly = true;

        self.wsParams = {
            page: null, page_size: null, started: null, ended: null, order: $rootScope.workspacesControllerOrder || '-last_modified', status: null, error_category: null, job_type_id: null, job_type_name: null, job_type_category: null, url: null
        };

        var defaultColumnDefs = [
            {
                field: 'id',
                displayName: 'id',
                enableFiltering: false,
                sortable: false,
                width: 60,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.id }}</div>'

            },{
                field: 'name',
                displayName: 'Name',
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.name }}</div>'
            },{
                field: 'created',
                displayName: 'Created (Z)',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.created }}</div>'
            },{
                field: 'last_modified',
                displayName: 'Last Modified (Z)',
                enableFiltering: false,
                cellTemplate: '<div class="ui-grid-cell-contents">{{ row.entity.last_modified }}</div>'
            },
        ];
        
        $scope.gridOptions = gridFactory.defaultGridOptions();
        $scope.gridOptions.paginationCurrentPage = parseInt(self.wsParams.page || 1);
        $scope.gridOptions.paginationPageSize = parseInt(self.wsParams.page_size) || $scope.gridOptions.paginationPageSize;
        var colDefs = $rootScope.colDefs ? $rootScope.colDefs : defaultColumnDefs;
        $scope.gridOptions.columnDefs = gridFactory.applySortConfig(colDefs, self.wsParams);
        $scope.gridOptions.data = $scope.workspaces;
        $scope.gridOptions.onRegisterApi = function (gridApi) {
            //set gridApi on scope
            $scope.gridApi = gridApi;
            $scope.gridApi.selection.on.rowSelectionChanged($scope, function (row) {
                if ($scope.actionClicked) {
                    $scope.actionClicked = false;
                } else {
                    $scope.$apply(function(){
                        $location.path('/workspaces/' + row.entity.id);
                    });
                }

            });
            $scope.gridApi.pagination.on.paginationChanged($scope, function (currentPage, pageSize) {
                self.wsParams.page = currentPage;
                self.wsParams.page_size = pageSize;
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

        $scope.cancelCreate = function(){
            $scope.mode = "view";
            $scope.activeWorkspace = null;
        };

        $scope.newWorkspace = function(){
            console.log('create new workspace');
            $scope.mode = "add";
          $scope.activeWorkspace =  {
              name: "",
              title: "",
              description: "",
              base_url: "",
              is_active: true,
              created: null,
              archived: null,
              last_modified: null
          }
        };

        var enableSaveWorkspace = function () {
            $scope.activeWorkspace.modified = true;
            $scope.saveBtnClass = 'btn-primary';
        };

        var disableSaveWorkspace = function () {
            $scope.activeWorkspace.modified = false;
            $scope.saveBtnClass = 'btn-default;'
        };

        $scope.$watchCollection('activeWorkspace', function (newValue, oldValue) {
            if(oldValue){
                enableSaveWorkspace();
            }

        });

        self.getWorkspaces = function () {
            $scope.loading = true;
            workspacesService.getWorkspaces().then(function (data) {
                $scope.workspaces = data;
                $scope.gridOptions.data = data;
                $scope.loading = false;
            }).catch(function (error) {
                $scope.loading = false;
                console.log(error);
            });
        };

        self.initialize = function () {
            self.getWorkspaces();
            $rootScope.user = userService.getUserCreds();

            if ($rootScope.user) {
                $scope.readonly = false;
            }
            navService.updateLocation('workspaces');
        };

        self.initialize();

    });
})();