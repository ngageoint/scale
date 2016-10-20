/**
 * <ais-scale-recipe-viewer />
 */
(function () {
    angular.module('scaleApp').controller('aisScaleRecipeGraphViewerController', function ($rootScope, $scope, $location, $uibModal, scaleConfig, scaleService, jobTypeService, recipeService, workspacesService, RecipeType, RecipeTypeDetail, JobType, localStorage) {
        var vm = this;
        
        vm.vertices = [];
        vm.edges = [];
        vm.selectedJob = null;
        vm.selectedInputProvider = null;
        vm.mode = null;
        vm.editMode = null;
        vm.dependencyBtnClass = 'fa-plus';
        vm.addBtnText = 'New Recipe';
        vm.addBtnClass = 'btn-primary';
        vm.addBtnIcon = 'fa-plus-circle';
        vm.editBtnText = 'Edit';
        vm.editBtnClass = 'btn-success';
        vm.editBtnIcon = 'fa-edit';
        vm.jobTypeValues = [];
        vm.saveBtnClass = 'btn-default';
        vm.savingRecipe = false;
        vm.warnings = [];
        vm.readonly = true;
        vm.detailMaxHeight = 0;
        vm.recipeTypeTrigger = { dataTypes: '' };
        vm.detailContainerStyle = '';
        vm.containerClass = $scope.hasContainer ? '' : 'detail-container no-tabs';
        vm.lastStatusChange = '';
        vm.availableWorkspaces = [];
        vm.recipeInputTypes = [
            {
                name: 'property',
                title: 'Property',
                fields: []
            },
            {
                name: 'file',
                title: 'File',
                fields: [
                    {
                        name: 'media_types',
                        title: 'Media Types',
                        value: []
                    }
                ]
            },
            {
                name: 'files',
                title: 'Files',
                fields: [
                    {
                        name: 'media_types',
                        title: 'Media Types',
                        value: []
                    }
                ]
            }
        ];
        vm.availableTriggerTypes = scaleConfig.triggerTypes;
        vm.selectedRecipeInputType = {};
        vm.recipeInput = {
            name: '',
            required: true,
            type: ''
        };
        vm.isIE = scaleService.isIE();

        var startJob = null;
        var zoomScale = 0;

        // Dagre variables
        var svg = null;
        var inner = null;
        var graph = null;
        var zoom = null;
        var render = null;

        var getClosestNode = function (name) {
            return d3.selectAll('.nodeRect').filter(function (d) {
                return d === name;
            });
        };

        var getOtherNodes = function (name) {
            return d3.selectAll('.nodeRect').filter(function (d) {
                return d !== name;
            });
        };

        var resetEditBtn = function () {
            vm.editBtnText = vm.mode === 'edit' ? 'Cancel Edit' : 'Edit';
            vm.editBtnClass = vm.mode === 'edit' ? 'btn-warning' : 'btn-success';
            vm.editBtnIcon = vm.mode === 'edit' ? 'fa-close' : 'fa-edit';
        };

        var resetAddBtn = function () {
            vm.addBtnText = vm.mode === 'add' ? 'Cancel' : 'New Recipe';
            vm.addBtnClass = vm.mode === 'add' ? 'btn-warning' : 'btn-primary';
            vm.addBtnIcon = vm.mode === 'add' ? 'fa-close' : 'fa-plus-circle';
        };

        var toggleAddRecipe = function () {
            vm.mode = vm.mode === 'add' ? 'view' : 'add';
            resetAddBtn();
        };

        var toggleEditRecipe = function () {
            if (vm.mode === 'edit') {
                vm.mode = 'view';
                vm.reloadRecipeTypeDetail($scope.recipeType.id);
            } else {
                vm.mode = 'edit';
            }
            vm.editMode = '';
            resetEditBtn();
        };

        var enableSaveRecipe = function () {
            $scope.recipeType.modified = true;
            vm.saveBtnClass = 'btn-success';
        };

        var disableSaveRecipe = function () {
            $scope.recipeType.modified = false;
            vm.saveBtnClass = 'btn-default;'
        };

        var confirmChangeRecipe = function () {
            var modalInstance = $uibModal.open({
                animation: vm.animationsEnabled,
                templateUrl: 'confirmDialog.html',
                scope: $scope,
                size: 'sm'
            });

            return modalInstance.result;
        };

        var getRecipeTypeJobClassName = function (job) {
            // default to 'nostatus'
            var className = 'nostatus';
            // find the associated job in the recipe.jobs
            if ($scope.recipe) {
                var recipejob = _.find($scope.recipe.jobs,{job_name: job.name});
                if (recipejob) {
                    className = recipejob.job.status.toLowerCase();
                }
            }
            return className;
        };

        vm.reloadRecipeTypeDetail = function (id) {
            var getRecipeDetail = function () {
                recipeService.getRecipeTypeDetail(id).then(function (data) {
                    $scope.recipeType = data;

                });
            };

            if ($scope.recipeType.modified) {
                confirmChangeRecipe().then(function () {
                    // OK
                    disableSaveRecipe();
                    resetAddBtn();
                    if (vm.mode === 'edit') {
                        toggleEditRecipe();
                    }
                    getRecipeDetail();
                }, function () {
                    // Cancel

                });
            } else {
                if (vm.mode === 'edit') {
                    toggleEditRecipe();
                }
                resetAddBtn();
                getRecipeDetail();
            }
        };

        vm.redraw = function () {
            initialize();
            //$rootScope.$broadcast('recipeModified');
        };

        vm.nodeClick = function (name) {
            // Remove selection class
            //$('div').removeClass('selected-node');
            d3.selectAll('.nodeRect').classed('selected-node', false);

            // find the job in the recipe definition
            var job = _.find($scope.recipeType.definition.jobs, { name: name });

            if (name === 'start') {
                job = startJob;
            }
            var $name = $('#' + name);
            var pos = $name.position();

            // click node different from selectedJob
            if (!vm.selectedJob || job.name !== vm.selectedJob.name) {
                if (vm.editMode === 'addDependency') {
                    addDependency(name);
                    enableSaveRecipe();
                    vm.redraw();

                } else if (vm.editMode === 'addInput') {
                    var contentStr = '';
                    if (job.name === 'start') {
                        contentStr = '<ul class="list-group">';
                        _.forEach($scope.recipeType.definition.input_data, function (recipeInput) {
                            contentStr = contentStr + '<li class="list-group-item">';
                            contentStr = contentStr + '<a onclick="mapInputRecipeInput(\'' + recipeInput.name + '\')">' + recipeInput.name + '</a>';
                            if (recipeInput.media_types) {
                                contentStr = contentStr + '<div class="input-media-types">' + recipeInput.media_types.join(',') + '</div>';
                            }
                            contentStr = contentStr + '</li>';
                        });
                        contentStr = contentStr + '</ul>';
                        $name.popover({
                            container: 'body',
                            content: contentStr,
                            html: true,
                            title: 'Select provider/output'
                        });
                        $name.popover('show');
                    } else {
                        if (job.job_type.job_type_interface.output_data.length > 0) {
                            contentStr = '<ul class="list-group">';
                            _.forEach(job.job_type.job_type_interface.output_data, function (jobOutput) {
                                contentStr = contentStr + '<li class="list-group-item">';
                                contentStr = contentStr + '<a onclick="mapInput(\'' + job.name + '\', \'' + jobOutput.name + '\')">' + jobOutput.name + '</a>';
                                if (jobOutput.media_type) {
                                    contentStr = contentStr + '<div class="input-media-types">' + jobOutput.media_type + '</div>';
                                }
                                contentStr = contentStr + '</li>';
                            });
                            contentStr = contentStr + '</ul>';
                            $name.popover({
                                container: 'body',
                                content: contentStr,
                                html: true,
                                title: 'Select provider/output'
                            });
                            $name.popover('show');
                        }
                    }
                } else if (vm.editMode === 'addOutput') {
                    vm.selectedOutputReceiver = job;
                    if (job.job_type.job_type_interface.input_data.length > 0) {
                        contentStr = '<ul class="list-group">';
                        _.forEach(job.job_type.job_type_interface.input_data, function (jobInput) {
                            contentStr = contentStr + '<li class="list-group-item">';
                            contentStr = contentStr + '<a onclick="mapOutput(\'' + job.name + '\', \'' + jobInput.name + '\')">' + jobInput.name + '</a>';
                            if (jobInput.media_types) {
                                contentStr = contentStr + '<div class="input-media-types">' + jobInput.media_types.join(',') + '</div>';
                            }
                            contentStr = contentStr + '</li>';
                        });
                        contentStr = contentStr + '</ul>';
                        $name.popover({
                            container: 'body',
                            content: contentStr,
                            html: true,
                            title: 'Select receiver/input'
                        });
                        $name.popover('show');
                    }
                } else {
                    // update the selected job
                    vm.selectedJob = job;
                    if ($scope.recipe) {
                        vm.selectedRecipeJob = _.find($scope.recipe.jobs, { job_name: job.name });
                    }
                    // apply the selected-node class
                    //$name.addClass('selected-node');
                    getClosestNode(name).classed('selected-node', true);
                }
            }
            else { // click selected node
                //$('div').removeClass('selected-node');
                d3.selectAll('.nodeRect').classed('selected-node', false);
                vm.selectedJob = null;
                vm.selectedRecipeJob = null;
                vm.selectedOutputReceiver = null;
                vm.selectedInputProvider = null;
                vm.editMode = '';
                vm.dependencyBtnClass = 'fa-plus';

                //$('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
                getOtherNodes(name).classed('selected-node-selectable', false);
            }
            if (vm.selectedJob) {
                //$('#' + vm.selectedJob.name).addClass('selected-node');
                getClosestNode(vm.selectedJob.name).classed('selected-node', true);
            }
        };
        vm.toggleEditMode = function () {
            if (vm.mode === 'edit') {
                vm.reloadRecipeTypeDetail($scope.recipeType.id);
            } else {
                toggleEditRecipe();
                resetAddBtn();
            }
            $rootScope.$broadcast('toggleEdit', vm.mode);
        };

        vm.openAddJob = function () {
            var modalInstance = $uibModal.open({
                animation: vm.animationsEnabled,
                templateUrl: 'addJobContent.html',
                scope: $scope,
                size: 'sm'
            });

            modalInstance.result.then(function () {
                if (vm.selectedJobType) {
                    jobTypeService.getJobTypeDetails(vm.selectedJobType.id).then(function (data) {
                        vm.addJobType(data);
                        enableSaveRecipe();
                    });
                }
            }, function () {

            });
        };

        vm.openEditTrigger = function () {
            var modalInstance = $uibModal.open({
                animation: vm.animationsEnabled,
                templateUrl: 'editTrigger.html',
                scope: $scope,
                size: 'md'
            });

            modalInstance.result.then(function () {
                if (vm.mode === 'edit' || vm.mode === 'add') {
                    $scope.recipeType.trigger_rule.configuration.condition.data_types = vm.recipeTypeTrigger.dataTypes ? vm.recipeTypeTrigger.dataTypes.split(',') : [];
                    enableSaveRecipe();
                }
            }, function () {

            });


        };

        vm.deleteRecipeInput = function (inputName) {
            var removedRecipeInput = _.remove($scope.recipeType.definition.input_data, function (recipeInput) {
                return recipeInput.name === inputName;
            });
            console.log('removed ' + removedRecipeInput.length + ' recipe inputs.');
            enableSaveRecipe();
            vm.redraw();

        };

        vm.openAddInput = function () {
            var modalInstance = $uibModal.open({
                animation: vm.animationsEnabled,
                templateUrl: 'addInput.html',
                scope: $scope
            });

            modalInstance.result.then(function () {
                // check for fields and add as necessary
                if ( vm.selectedRecipeInputType.fields.length > 0) {
                    var fieldArr = [];
                    _.forEach(vm.selectedRecipeInputType.fields, function (field) {
                        _.forEach(field.value.split(','), function (value) {
                            fieldArr.push(value);
                        });
                        vm.recipeInput[field.name] = fieldArr;
                    });
                }

                // add input to recipe type definition
                $scope.recipeType.definition.input_data.push(vm.recipeInput);
                _.forEach($scope.recipeType.definition.jobs, function (job) {
                    if (job.recipe_inputs.length === 0) {
                        job.recipe_inputs.push({
                            job_input: vm.recipeInput.name,
                            recipe_input: vm.recipeInput.name
                        });
                    }
                });
                getIoMappings();

                // reset form fields
                vm.recipeInput = {
                    name: '',
                    required: true,
                    type: ''
                };
                vm.selectedRecipeInputType = {};
            });
        };

        vm.changeInputType = function () {
            vm.selectedRecipeInputType = _.find(vm.recipeInputTypes, {'name': vm.recipeInput.type});
        };

        var getWarningsHtml = function (warnings) {
            var warningsHtml = '';
            _.forEach(warnings, function (warning) {
                warningsHtml += '<b>' + warning.id + ':</b> ' + warning.details + '<br /><br />';
            });
            warningsHtml += '<button type="button" class="btn btn-default btn-xs clear">Hide</button>';
            return warningsHtml;
        };

        vm.validateRecipeType = function () {
            recipeService.validateRecipeType($scope.recipeType).then(function (validationResult) {
                if (validationResult.warnings && validationResult.warnings.length > 0) {
                    // display the warnings
                    var warningsHtml = getWarningsHtml(validationResult.warnings);
                    toastr["warning"](warningsHtml);
                } else {
                    toastr["success"]('Recipe is valid.');
                }
            }).catch(function (error) {
                if (error.detail) {
                    toastr["error"](error.detail);
                } else {
                    toastr["error"](error);
                }
            });

        };


        vm.saveRecipeType = function () {
            vm.savingRecipe = true;
            recipeService.validateRecipeType($scope.recipeType).then(function (validationResult) {
                if (validationResult.warnings && validationResult.warnings.length > 0) {
                    // display the warnings
                    var warningsHtml = getWarningsHtml(validationResult.warnings);
                    toastr["warning"](warningsHtml);
                    vm.savingRecipe = false;
                }
                recipeService.saveRecipeType($scope.recipeType).then(function (saveResult) {
                    vm.savingRecipe = false;
                    $scope.recipeType = RecipeTypeDetail.transformer(saveResult);
                    if (scaleConfig.static) {
                        console.log(JSON.stringify($scope.recipeType));
                        localStorage.setItem('recipeType' + $scope.recipeType.id, JSON.stringify($scope.recipeType));
                    }
                    vm.redraw();
                    $location.path('/recipes/types/' + $scope.recipeType.id);
                });
            }).catch(function (error) {
                if (error && error.detail) {
                    toastr['error'](error.detail);
                } else {
                    toastr['error'](error);
                }
                vm.savingRecipe = false;
            });

            disableSaveRecipe();
        };

        vm.addJobType = function (selectedJobType) {
            console.log(selectedJobType.name);
            $scope.recipeType.definition.addJob(selectedJobType);
            //$scope.$broadcast('redrawRecipes');
            vm.redraw();
        };

        vm.mapInput = function (providerName, providerOutput) {
            console.log('map selected job input to ' + providerName + '.' + providerOutput);
            var dependency = _.find(vm.selectedJob.dependencies, {name: providerName});

            if (dependency && dependency.connections && dependency.connections.length > 0) {
                var conn = _.find(dependency.connections, { output: providerOutput, input: vm.selectedJobInput.name });
                if (!conn) {
                    dependency.connections.push({ output: providerOutput, input: vm.selectedJobInput.name });
                }
            }
            else if (!dependency) {
                dependency = {name: providerName, connections: [{ output: providerOutput, input: vm.selectedJobInput.name }]};
                vm.selectedJob.dependencies.push(dependency);
            }
            else {
                dependency.connections = [{ output: providerOutput, input: vm.selectedJobInput.name }];
            }
            vm.selectedJob.depStart = false;
            vm.editMode = '';
            vm.selectedJobInput = null;
            vm.selectedInputProvider = null;
            enableSaveRecipe();
            vm.redraw();
        };

        vm.mapInputRecipeInput = function (recipeInput) {
            console.log('map selected job to recipe input ' + recipeInput);
            var existingInput = _.find(vm.selectedJob.recipe_inputs, { job_input: vm.selectedJobInput.name });
            if ( existingInput && existingInput.recipe_name !== recipeInput) {
                // update it
                existingInput.recipe_input = recipeInput;
                enableSaveRecipe();
                vm.redraw();
            } else if ( !existingInput ) {
                // create it
                vm.selectedJob.recipe_inputs.push({
                    job_input: vm.selectedJobInput.name,
                    recipe_input: recipeInput
                });
                enableSaveRecipe();
                vm.redraw();
            }
            vm.editMode = '';
            vm.selectedJobInput = null;
            vm.selectedInputProvider = null;
        };

        vm.mapOutput = function (receiverName, receiverInput) {
            var dependency = _.find(vm.selectedOutputReceiver.dependencies, {name: vm.selectedJob.name});

            if (dependency && dependency.connections && dependency.connections.length > 0) {
                var conn = _.find(dependency.connections, { output: vm.selectedJobOutput.name, input: receiverInput });
                if (!conn) {
                    dependency.connections.push({output: vm.selectedJobOutput.name, input: receiverInput});
                }
            }
            else if (!dependency) {
                dependency = {name: vm.selectedJob.name, connections: [{output: vm.selectedJobOutput.name, input: receiverInput}]};
                vm.selectedOutputReceiver.dependencies.push(dependency);
            }
            else {
                dependency.connections = [{output: vm.selectedJobOutput.name, input: receiverInput}];
            }
            vm.selectedOutputReceiver.depStart = false;
            vm.editMode = '';
            vm.selectedJobOutput = null;
            vm.selectedOutputReceiver = null;
            enableSaveRecipe();
            vm.redraw();
        };

        vm.toggleAddDependency = function () {
            if (vm.editMode === 'addDependency') {
                vm.editMode = '';
                vm.dependencyBtnClass = 'fa-plus';
                getOtherNodes(vm.selectedJob.name).classed('selected-node-selectable', false);
                //$('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
            } else {
                console.log('toggle addDependency mode');
                vm.editMode = 'addDependency';
                vm.dependencyBtnClass = 'fa-remove';
                getOtherNodes(vm.selectedJob.name).classed('selected-node-selectable', true);
                //$('.recipeNode:not(".selected-node")').addClass('selected-node-selectable');
            }
        };

        vm.toggleAddInput = function (jobinput) {
            if (vm.editMode === 'addInput') {
                vm.editMode = '';
                getOtherNodes(vm.selectedJob.name).classed('selected-node-selectable', false);
                //$('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
            } else {
                vm.selectedJobInput = jobinput;
                console.log('toggle addInput mode');
                vm.editMode = 'addInput';
                getOtherNodes(vm.selectedJob.name).classed('selected-node-selectable', true);
                //$('.recipeNode:not(".selected-node")').addClass('selected-node-selectable');
            }
        };

        vm.toggleAddOutput = function (joboutput) {
            if (vm.editMode === 'addOutput') {
                vm.editMode = '';
                getOtherNodes(vm.selectedJob.name).classed('selected-node-selectable', false);
                //$('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
            } else {
                vm.selectedJobOutput = joboutput;
                console.log('toggle addOutput mode');
                vm.editMode = 'addOutput';
                getOtherNodes(vm.selectedJob.name).classed('selected-node-selectable', true);
                //$('.recipeNode:not(".selected-node")').addClass('selected-node-selectable');
            }
        };

        vm.removeDependency = function (depName) {
            var removedDeps = _.remove(vm.selectedJob.dependencies, function (dep) {
                return dep.name === depName;
            });
            console.log('removed ' + removedDeps.length + ' dependencies.');
            enableSaveRecipe();
            vm.redraw();
        };

        vm.removeInputMapping = function (depName, depOutput) {
            if ( depName === 'recipe' ) {
                // remove it from selectedJob.recipe_inputs
                var dep = _.remove(vm.selectedJob.recipe_inputs, { recipe_input: depOutput });
                enableSaveRecipe();
                vm.redraw();
            } else {
                var dep = _.find(vm.selectedJob.dependencies, {name: depName});
                if (dep && dep.connections) {
                    // it's an input from another job
                    var removedCon = _.remove(dep.connections, function (conn) {
                        return conn.output === depOutput;
                    });
                    console.log('removed ' + removedCon.length + ' input connections.');
                    enableSaveRecipe();
                    vm.redraw();
                }
            }

        };

        vm.deleteRecipeJob = function (jobName) {
            // remove dependent connections
            _.forEach($scope.recipeType.definition.jobs, function (job) {
                _.remove(job.dependencies, {name: jobName});
            });
            // remove job from definition.jobs
            _.remove($scope.recipeType.definition.jobs, { name: jobName });
            // enable save and redraw
            vm.selectedJob = null;
            enableSaveRecipe();
            vm.redraw();
        };

        vm.removeOutputMapping = function (jobName, depOutput) {
            // we have to remove output mapping from the job where the dependency is defined
            var receiver = _.find($scope.recipeType.definition.jobs,{name: jobName});
            // remove it from receiver.dependencies
            var dep = _.find(receiver.dependencies, {name: vm.selectedJob.name});
            if (dep && dep.connections) {
                var removedCon = _.remove(dep.connections, function (conn) {
                    return conn.output === depOutput;
                });
                console.log('removed ' + removedCon.length + ' output connections.');
                enableSaveRecipe();
                vm.redraw();
            }
        };

        vm.selectJobTypeToAdd = function (item) {
            vm.selectedJobType = item;
        };

        $scope.$on('redrawRecipes', function () {
            vm.redraw();
        });

        var addDependency = function (jobName) {
            console.log(vm.selectedJob.name + '->' + jobName);
            if (!vm.selectedJob.dependencies) {
                vm.selectedJob.dependencies = [];
            }
            var existingDependency = _.find(vm.selectedJob.dependencies, {name: jobName});

            if (!existingDependency) { vm.selectedJob.dependencies.push({name: jobName}); }
            vm.selectedJob.depStart = false;
            vm.editMode = '';
            vm.dependencyBtnClass = 'fa-plus';

        };

        var getIoMappings = function () {
            if ($scope.recipeType.definition) {
                _.forEach($scope.recipeType.definition.jobs, function (job) {
                    // populate the current jobType
                    /*var thisJobType = _.find($scope.recipeType.job_types,{id: job.job_type_id});
                    job.job_type = thisJobType;*/

                    // find dependents
                    if (job.job_type && job.job_type.job_type_interface) {
                        _.forEach(job.job_type.job_type_interface.output_data, function (jobOutput, key) {
                            if (jobOutput) {
                                var deps = getDependents(job.name,jobOutput.name);
                                jobOutput.dependents = deps;
                            }
                        });
                        // add dependency mappings
                        _.forEach(job.job_type.job_type_interface.input_data, function (jobInput, key) {
                            if (jobInput) {
                                var inputMappings = [];
                                _.forEach(job.dependencies, function (dependency,key) {
                                    _.forEach(dependency.connections, function (conn,key) {
                                        if (conn.input === jobInput.name) {
                                            inputMappings.push({
                                                name: dependency.name,
                                                output: conn.output,
                                                input: conn.input
                                            });
                                        }
                                    });
                                });
                                _.forEach(job.recipe_inputs, function (recipeInput, key) {
                                    if (recipeInput.job_input === jobInput.name) {
                                        inputMappings.push({
                                            name: 'recipe',
                                            output: recipeInput.recipe_input,
                                            input: recipeInput.job_input
                                        });
                                    }
                                });
                                jobInput.dependencies = inputMappings;
                            }
                        });

                    }
                });
            }

        };

        var initialize = function () {

            jobTypeService.getJobTypesOnce().then(function (data) {
                vm.jobTypeValues = data.results;
            });

            workspacesService.getWorkspaces().then(function (data) {
                vm.availableWorkspaces = data
            });

            $scope.$watchCollection('recipeType', function (newValue, oldValue) {
                if (!$scope.recipeType) {
                    $scope.recipeType = new RecipeType();
                }

                if (typeof $scope.recipeType.id === 'undefined' || $scope.recipeType.id === null || $scope.recipeType.id === 0) {
                    vm.mode = 'add';
                } else {
                    if (vm.mode !== 'edit') {
                        vm.mode = 'view'
                    }
                }
                _.forEach($scope.recipeType.definition.jobs, function (job, idx) {
                    if (!job.job_type.job_type_interface && $scope.recipeType.job_types) {
                        var jobTypeData = _.find($scope.recipeType.job_types, {name: job.job_type.name, version: job.job_type.version});
                        $scope.recipeType.definition.jobs[idx].job_type = jobTypeData;
                    }
                });

                // setup string to bind comma delimited list of trigger rule configuration condition data types
                if ($scope.recipeType.trigger_rule) {
                    if ($scope.recipeType.trigger_rule.configuration) {
                        if ($scope.recipeType.trigger_rule.configuration.condition) {
                            if ($scope.recipeType.trigger_rule.configuration.condition.data_types) {
                                vm.recipeTypeTrigger.dataTypes = $scope.recipeType.trigger_rule.configuration.condition.data_types.join(',');
                            }
                        }
                    }
                }

                initGraph();
                getIoMappings();
                drawGraph();
            });
            if ($scope.$parent.vm.user) {
                vm.readonly = false;
            }
        };

        var initGraph = function () {
            // ******
            // setup D3 container and Graph
            // ******
            //vm.selectedJob = null;
            function clicked() {
                var d = d3.event;
                var x = d3.event.x;
                var y = d3.event.y;
                var width = parseInt(svg.style("width").replace(/px/, ""));
                var height = parseInt(svg.style("height").replace(/px/, ""));

                inner.attr("transform", "translate(" + width / 2 + "," + height / 2 + ")scale(2)translate(" + -x + "," + -y + ")");

                //inner.attr("transform", "translate(50px, 50px)scale(2,3)");

                console.log(d);
            }

            svg = d3.select("svg");
            inner = svg.select("g"); //.on("click", clicked);
            // Set up zoom support
            zoom = d3.behavior.zoom().on("zoom", function () {
                zoomScale = d3.event.scale;
                inner.attr("transform", "translate(" + d3.event.translate + ")" +
                    "scale(" + zoomScale + ")");
            });
            svg.call(zoom);

            render = new dagreD3.render();

            // Left-to-right layout
            graph = new dagreD3.graphlib.Graph();
            graph.setGraph({
                nodesep: 70,
                ranksep: 50,
                rankdir: "TB",
                marginx: 20,
                marginy: 20
            });
        };

        drawGraph = function () {
            // globals because dagre needs a reference to angular scope
            window.nodeClick = function (name) {
                var scope = angular.element(document.getElementById('recipeviewer')).scope();
                scope.$apply(function () {
                    scope.vm.nodeClick(name);
                });
            };

            window.mapInput = function (jobName, jobOutput) {
                $('#' + jobName).popover('destroy');
                var scope = angular.element(document.getElementById('recipeviewer')).scope();
                scope.$apply(function () {
                    scope.vm.mapInput(jobName, jobOutput);
                });
            };

            window.mapInputRecipeInput = function (recipeInputName) {
                $('#start').popover('destroy');
                var scope = angular.element(document.getElementById('recipeviewer')).scope();
                scope.$apply(function () {
                    scope.vm.mapInputRecipeInput(recipeInputName);
                });
            };

            window.mapOutput = function (jobName, jobInput) {
                $('#' + jobName).popover('destroy');
                var scope = angular.element(document.getElementById('recipeviewer')).scope();
                scope.$apply(function () {
                    scope.vm.mapOutput(jobName, jobInput);
                });
            };

            if ($scope.recipe) {
                vm.lastStatusChange = $scope.recipe.last_modified ? moment.duration(moment.utc($scope.recipe.last_modified).diff(moment.utc())).humanize(true) : '';
            }

            var jobs = [];
            if ($scope.recipeType.definition) {
                jobs = $scope.recipeType.definition.jobs;
            }
            var childCounts = [];
            // create graph objects
            for (var idx in jobs) {
                var job = jobs[idx];

                if (job.dependencies === undefined || job.dependencies.length < 1) {
                    job.depStart = true;
                }
                var className = getRecipeTypeJobClassName(job);

                var html = '<div class="recipeNode">';
                //var html = "<div onclick=\"console.log('" + job.job_type.name + "')\">";
                if (className !== 'nostatus') {
                    html += '<span class="status"></span>';
                }
                //   html += "<span class=consumers>"+worker.consumers+"</span>";
                html += '<span class="name">';
                if (job.job_type) {
                    //console.log(job.jobType);
                    html += '<div id="' + job.name + '" class="" onclick="nodeClick(\'' + job.name + '\')"><span class="name">' + job.job_type.getIcon() + ' ' + job.name + '</span></div>';
                    //if (jobType.name) {
                    //    html += '<div id="' + job.name + '" class="recipeNode" onclick="nodeClick(\'' + job.name + '\')"><span class="name">' + jobType.getIcon() + ' ' + jobType.title + '</span></div>';
                    //} else {
                    //    html += '<div id="' + job.name + '" class="recipeNode" onclick="nodeClick(\'' + job.name + '\')"><span class="name">' + jobType.getIcon() + ' ' + job.name + '</span></div>';
                    //}

                }
                html += '</span>';
                //   html += "<span class=queue><span class=counter>"+worker.count+"</span></span>";
                html += '</div>';
                graph.setNode(job.name, {
                    labelType: 'html',
                    label: html,
                    rx: 5,
                    ry: 5,
                    padding: 0,
                    class: className
                });
                // setup edges
                for (var d in job.dependencies) {
                    var dep = job.dependencies[d];

                    if (dep.name) {
                        graph.setEdge(dep.name, job.name, {
                            //labelType: 'html',
                            //label: dep.name + '-->' + job.name,
                            width: 20

                        });
                        if (childCounts[dep.name]) {
                            childCounts[dep.name] += 1;
                        } else {
                            childCounts[dep.name] = 1;
                        }
                    }
                }
            }

            // set start node and edges
            graph.setNode('start', {
                labelType: 'html',
                label: '<div id="start" class="recipeNode" onclick="nodeClick(\'start\')"><span class=name>Start</span></div>',
                rx: 5,
                ry: 5,
                padding: 0
            });
            startJob = {
                name: 'start',
                job_type: {
                    title: 'Start'
                },
                input_data: $scope.recipeType.input_data
            };
            var noDeps = _.filter(jobs, 'depStart', true);
            for (var n in noDeps) {
                graph.setEdge('start', noDeps[n].name, {
                    width: 20
                });
            }

            // set end node and edges
            graph.setNode('end', {
                labelType: 'html',
                label: '<div class="recipeNode"><span class="name">End</span></div>',
                rx: 5,
                ry: 5,
                padding: 0
            });
            var noChildren =_.filter(jobs, function (job) {
                return !childCounts[job.name];
            });
            for (var o in noChildren) {
                graph.setEdge(noChildren[o].name, 'end', {
                    width: 20
                });
            }

            // wait for current call stack to clear
            _.defer(function () {
                inner.call(render, graph);
                zoom.event(d3.select("svg"));

                $('.node rect').attr('class', 'nodeRect');

                // add selected class to appropriate node
                if (vm.selectedJob) {
                    //$('#' + vm.selectedJob.name).addClass('selected-node');
                    getClosestNode(vm.selectedJob.name).classed('selected-node', true);
                }
            });
        };

        var getDependents = function (name,outputName) {
            var results = [];

            _.forEach($scope.recipeType.definition.jobs, function (job, key) {
                if (job.name !== name) {
                    _.forEach(job.dependencies, function (dependency, key) {
                        if (dependency.name === name) {
                            _.forEach(dependency.connections, function (conn, key) {
                                if (conn.output === outputName) {
                                    results.push({
                                        name: job.name,
                                        output: conn.output,
                                        input: conn.input
                                    });
                                }
                            });
                        }
                    });
                }
            });
            return results;
        };

        initialize();

    }).directive('aisScaleRecipeGraphViewer', function () {
        'use strict';
        /**
         * Usage: <ais-scale-recipe-viewer recipe="recipe" />
         */
        return {
            controller: 'aisScaleRecipeGraphViewerController',
            controllerAs: 'vm',
            templateUrl: 'modules/recipes/partials/recipeGraphViewerTemplate.html',
            restrict: 'E',
            scope: {
                recipeType: '=',
                recipe: '=',
                isModified: '=modified',
                allowEdit: '=',
                hasContainer: '='
            }
        };

    });
})();
