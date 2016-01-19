/**
 * <ais-scale-recipe-viewer />
 */
(function () {
    angular.module('scaleApp').controller('aisScaleRecipeGraphViewerController', function ($rootScope, $scope, $location, $modal, scaleConfig, scaleService, jobTypeService, recipeService, workspacesService) {
        $scope.vertices = [];
        $scope.edges = [];
        $scope.isUpdate = false;
        $scope.selectedJob = null;
        $scope.selectedInputProvider = null;
        $scope.mode = null;
        $scope.editMode = null;
        $scope.dependencyBtnClass = 'fa-plus';
        $scope.addBtnText = 'New Recipe';
        $scope.addBtnClass = 'btn-primary';
        $scope.addBtnIcon = 'fa-plus-circle';
        $scope.editBtnText = 'Edit';
        $scope.editBtnClass = 'btn-success';
        $scope.editBtnIcon = 'fa-edit';
        $scope.jobTypeValues = [];
        $scope.saveBtnClass = 'btn-default';
        $scope.savingRecipe = false;
        $scope.warnings = [];
        $scope.readonly = true;
        $scope.detailMaxHeight = 0;
        $scope.recipeTypeTrigger = { dataTypes: '' };
        $scope.detailContainerStyle = '';
        $scope.containerClass = $scope.hasContainer ? '' : 'detail-container no-tabs';
        $scope.lastStatusChange = '';
        $scope.availableWorkspaces = [];
        $scope.recipeInputTypes = [
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
        $scope.availableTriggerTypes = scaleConfig.triggerTypes;
        $scope.selectedRecipeInputType = {};
        $scope.recipeInput = {
            name: '',
            required: true,
            type: ''
        };
        $scope.isIE = scaleService.isIE();

        var startJob = null;

        // Dagre variables
        var svg = null;
        var inner = null;
        var graph = null;
        var zoom = null;
        var render = null;


        var resetEditBtn = function () {
            $scope.editBtnText = $scope.mode === 'edit' ? 'Cancel Edit' : 'Edit';
            $scope.editBtnClass = $scope.mode === 'edit' ? 'btn-warning' : 'btn-success';
            $scope.editBtnIcon = $scope.mode === 'edit' ? 'fa-close' : 'fa-edit';
        };

        var resetAddBtn = function () {
            $scope.addBtnText = $scope.mode === 'add' ? 'Cancel' : 'New Recipe';
            $scope.addBtnClass = $scope.mode === 'add' ? 'btn-warning' : 'btn-primary';
            $scope.addBtnIcon = $scope.mode === 'add' ? 'fa-close' : 'fa-plus-circle';
        };

        var toggleAddRecipe = function () {
            $scope.mode = $scope.mode === 'add' ? 'view' : 'add';
            resetAddBtn();
        };

        var toggleEditRecipe = function () {
            if($scope.mode === 'edit'){
                $scope.mode = 'view';
                $scope.reloadRecipeTypeDetail($scope.recipeType.id);
            } else {
                $scope.mode = 'edit';
            }
            $scope.editMode = '';
            resetEditBtn();
        };

        var enableSaveRecipe = function () {
            $scope.recipeType.modified = true;
            $scope.saveBtnClass = 'btn-success';
        };

        var disableSaveRecipe = function () {
            $scope.recipeType.modified = false;
            $scope.saveBtnClass = 'btn-default;'
        };

        var confirmChangeRecipe = function () {
            var modalInstance = $modal.open({
                animation: $scope.animationsEnabled,
                templateUrl: 'confirmDialog.html',
                scope: $scope,
                size: 'sm'
            });

            return modalInstance.result;
        };

        var getRecipeTypeJobClassName = function(job){
            // default to 'nostatus'
            var className = 'nostatus';
            // find the associated job in the recipe.jobs
            if($scope.recipe){
                var recipejob = _.find($scope.recipe.jobs,{job_name: job.name});
                if(recipejob){
                    className = recipejob.job.status.toLowerCase();
                }
            }
            return className;
        };

        $scope.reloadRecipeTypeDetail = function (id) {
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
                    if ($scope.mode === 'edit') {
                        toggleEditRecipe();
                    }
                    getRecipeDetail();
                }, function () {
                    // Cancel

                });
            } else {
                if ($scope.mode === 'edit') {
                    toggleEditRecipe();
                }
                resetAddBtn();
                getRecipeDetail();
            }
        };

        $scope.redraw = function () {
            initialize();
            //$rootScope.$broadcast('recipeModified');
        };

        $scope.nodeClick = function (name) {
            // Remove selection class
            $('div').removeClass('selected-node');
            $('div').removeClass('selected-node-dependency');
            $('div').removeClass('job-active');

            // find the job in the recipe definition
            var job = _.find($scope.recipeType.definition.jobs,{name: name});

            if(name === 'start'){
                job = startJob;
            }
            var $name = $('#' + name);
            var pos = $name.position();

            // click node different from selectedJob
            if (!$scope.selectedJob || job.name !== $scope.selectedJob.name) {
                if ($scope.editMode === 'addDependency') {
                    addDependency(name);
                    enableSaveRecipe();
                    $scope.redraw();

                } else if ($scope.editMode === 'addInput') {
                    $scope.selectedInputProvider = job;
                    $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
                    $('#' + name).addClass('selected-node-dependency');
                    $('#output-selector').css({top: pos.top, left: pos.left, position: 'absolute'});
                    console.log('toggle input selector');
                } else if ($scope.editMode === 'addOutput'){
                    $scope.selectedOutputReceiver = job;
                    // set position of output-selector
                    $('#input-selector').css({top: pos.top, left: pos.left, position: 'absolute'});
                    //$scope.mode = 'addInputActive';
                    $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
                    $('#' + name).addClass('selected-node-dependency');
                    console.log('toggle output selector');
                } else {
                    // update the selected job
                    $scope.selectedJob = job;
                    if($scope.recipe){
                        $scope.selectedRecipeJob = _.find($scope.recipe.jobs, { job_name: job.name });
                    }
                    // apply the selected-node class
                    $name.addClass('selected-node');
                }
            }
            else { // click selected node
                $('div').removeClass('selected-node');
                $scope.selectedJob = null;
                $scope.selectedRecipeJob = null;
                $scope.selectedOutputReceiver = null;
                $scope.selectedInputProvider = null;
                $scope.editMode = '';
                $scope.dependencyBtnClass = 'fa-plus';

                $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
            }
            if($scope.selectedJob){
                $('#' + $scope.selectedJob.name).addClass('selected-node');
            }
        };
        $scope.toggleEditMode = function () {
            if ($scope.mode === 'edit') {
                $scope.reloadRecipeTypeDetail($scope.recipeType.id);
            } else {
                toggleEditRecipe();
                resetAddBtn();
            }
            $rootScope.$broadcast('toggleEdit', $scope.mode);
        };

        $scope.openAddJob = function () {
            var modalInstance = $modal.open({
                animation: $scope.animationsEnabled,
                templateUrl: 'addJobContent.html',
                scope: $scope,
                size: 'sm'
            });

            modalInstance.result.then(function () {
                if($scope.selectedItem){
                    jobTypeService.getJobTypeDetails($scope.selectedItem.id).then(function(data){
                        $scope.addJobType(data);
                        enableSaveRecipe();
                    });
                }
            }, function () {

            });
        };

        $scope.openEditTrigger = function () {
            var modalInstance = $modal.open({
                animation: $scope.animationsEnabled,
                templateUrl: 'editTrigger.html',
                scope: $scope,
                size: 'md'
            });

            modalInstance.result.then(function () {
                if( $scope.mode === 'edit' || $scope.mode === 'add' ) {
                    $scope.recipeType.trigger_rule.configuration.condition.data_types = $scope.recipeTypeTrigger.dataTypes ? $scope.recipeTypeTrigger.dataTypes.split(',') : [];
                    enableSaveRecipe();
                }
            }, function () {

            });


        };

        $scope.deleteRecipeInput = function(inputName){
            var removedRecipeInput = _.remove($scope.recipeType.definition.input_data, function (recipeInput) {
                return recipeInput.name === inputName;
            });
            console.log('removed ' + removedRecipeInput.length + ' recipe inputs.');
            enableSaveRecipe();
            $scope.redraw();

        };

        $scope.openAddInput = function(){
            var modalInstance = $modal.open({
                animation: $scope.animationsEnabled,
                templateUrl: 'addInput.html',
                scope: $scope
            });

            modalInstance.result.then(function(){
                // check for fields and add as necessary
                if( $scope.selectedRecipeInputType.fields.length > 0){
                    var fieldArr = [];
                    _.forEach($scope.selectedRecipeInputType.fields, function(field){
                        _.forEach(field.value.split(','), function(value){
                            fieldArr.push(value);
                        });
                        $scope.recipeInput[field.name] = fieldArr;
                    });
                }

                // add input to recipe type definition
                $scope.recipeType.definition.input_data.push($scope.recipeInput);
                _.forEach($scope.recipeType.definition.jobs, function(job){
                    if(job.recipe_inputs.length === 0){
                        job.recipe_inputs.push({
                            job_input: $scope.recipeInput.name,
                            recipe_input: $scope.recipeInput.name
                        });
                    }
                });
                getIoMappings();

                // reset form fields
                $scope.recipeInput = {
                    name: '',
                    required: true,
                    type: ''
                };
                $scope.selectedRecipeInputType = {};
            });
        };

        $scope.changeInputType = function(){
            $scope.selectedRecipeInputType = _.find($scope.recipeInputTypes, {'name': $scope.recipeInput.type});
        };

        var getWarningsHtml = function (warnings) {
            var warningsHtml = '';
            _.forEach(warnings, function (warning) {
                warningsHtml += '<b>' + warning.id + ':</b> ' + warning.details + '<br /><br />';
            });
            warningsHtml += '<button type="button" class="btn btn-default btn-xs clear">Hide</button>';
            return warningsHtml;
        };

        $scope.validateRecipeType = function () {
            recipeService.validateRecipeType($scope.recipeType).then(function(validationResult){
                if(validationResult.warnings && validationResult.warnings.length > 0){
                    // display the warnings
                    var warningsHtml = getWarningsHtml(validationResult.warnings);
                    toastr["error"](warningsHtml);
                } else {
                    toastr["success"]('Recipe is valid.');
                }
            }).catch(function(error){
                if(error.detail){
                    toastr["error"](error.detail);
                } else {
                    toastr["error"](error);
                }
            });

        };


        $scope.saveRecipeType = function () {
            $scope.savingRecipe = true;
            console.log('save recipe: ' + $scope.recipeType.name);
            recipeService.validateRecipeType($scope.recipeType).then(function(validationResult){
                if(validationResult.warnings && validationResult.warnings.length > 0){
                    // display the warnings
                    var warningsHtml = getWarningsHtml(validationResult.warnings);
                    toastr["error"](warningsHtml);
                    $scope.savingRecipe = false;
                } else {
                    recipeService.saveRecipeType($scope.recipeType).then(function(saveResult){
                        $scope.savingRecipe = false;
                        $scope.recipeType = saveResult;
                        $scope.redraw();
                        //$location.path('/recipes/types/' + saveResult.id);
                    });
                }
            }).catch(function(error){
                if(error.detail){
                    toastr['error'](error.detail);
                } else {
                    toastr['error'](error);
                }
                $scope.savingRecipe = false;
            });

            disableSaveRecipe();
        };

        $scope.addJobType = function (selectedJobType) {
            $scope.recipeType.definition.addJob(selectedJobType);
            $scope.$broadcast('redrawRecipes');
        };

        $scope.mapInput = function (providerName, providerOutput) {
            console.log('map selected job input to ' + providerName + '.' + providerOutput);
            var dependency = _.find($scope.selectedJob.dependencies, {name: providerName});

            if(dependency && dependency.connections && dependency.connections.length > 0){
                var conn = _.find(dependency.connections, { output: providerOutput, input: $scope.selectedJobInput.name });
                if(!conn){
                    dependency.connections.push({ output: providerOutput, input: $scope.selectedJobInput.name });
                }
            }
            else if(!dependency){
                dependency = {name: providerName, connections: [{ output: providerOutput, input: $scope.selectedJobInput.name }]};
                $scope.selectedJob.dependencies.push(dependency);
            }
            else {
                dependency.connections = [{ output: providerOutput, input: $scope.selectedJobInput.name }];
            }
            $scope.selectedJob.depStart = false;
            $scope.editMode = '';
            $scope.selectedJobInput = null;
            $scope.selectedInputProvider = null;
            enableSaveRecipe();
            $scope.redraw();
        };

        $scope.mapInputRecipeInput = function(recipeInput){
            console.log('map selected job to recipe input ' + recipeInput);
            var existingInput = _.find($scope.selectedJob.recipe_inputs, { job_input: $scope.selectedJobInput.name });
            if( existingInput && existingInput.recipe_name !== recipeInput){
                // update it
                existingInput.recipe_input = recipeInput;
                enableSaveRecipe();
                $scope.redraw();
            } else if( !existingInput ){
                // create it
                $scope.selectedJob.recipe_inputs.push({
                    job_input: $scope.selectedJobInput.name,
                    recipe_input: recipeInput
                });
                enableSaveRecipe();
                $scope.redraw();
            }
            $scope.editMode = '';
            $scope.selectedJobInput = null;
            $scope.selectedInputProvider = null;
        };

        $scope.mapOutput = function (receiverName, receiverInput) {
            var dependency = _.find($scope.selectedOutputReceiver.dependencies, {name: $scope.selectedJob.name});

            if(dependency && dependency.connections && dependency.connections.length > 0){
                var conn = _.find(dependency.connections, { output: $scope.selectedJobOutput.name, input: receiverInput });
                if(!conn){
                    dependency.connections.push({output: $scope.selectedJobOutput.name, input: receiverInput});
                }
            }
            else if(!dependency){
                dependency = {name: $scope.selectedJob.name, connections: [{output: $scope.selectedJobOutput.name, input: receiverInput}]};
                $scope.selectedOutputReceiver.dependencies.push(dependency);
            }
            else {
                dependency.connections = [{output: $scope.selectedJobOutput.name, input: receiverInput}];
            }
            $scope.selectedOutputReceiver.depStart = false;
            $scope.editMode = '';
            $scope.selectedJobOutput = null;
            $scope.selectedOutputReceiver = null;
            enableSaveRecipe();
            $scope.redraw();
        };

        $scope.toggleAddDependency = function () {
            if ($scope.editMode === 'addDependency') {
                $scope.editMode = '';
                $scope.dependencyBtnClass = 'fa-plus';
                $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
            } else {
                console.log('toggle addDependency mode');
                $scope.editMode = 'addDependency';
                $scope.dependencyBtnClass = 'fa-minus';
                $('.recipeNode:not(".selected-node")').addClass('selected-node-selectable');
            }
        };

        $scope.toggleAddInput = function (jobinput) {
            if ($scope.editMode === 'addInput') {
                $scope.editMode = '';
                $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
            } else {
                $scope.selectedJobInput = jobinput;
                console.log('toggle addInput mode');
                $scope.editMode = 'addInput';
                $('.recipeNode:not(".selected-node")').addClass('selected-node-selectable');
            }
        };

        $scope.toggleAddOutput = function (joboutput) {
            if ($scope.editMode === 'addOutput') {
                $scope.editMode = '';
                $('.recipeNode:not(".selected-node")').removeClass('selected-node-selectable');
            } else {
                $scope.selectedJobOutput = joboutput;
                console.log('toggle addOutput mode');
                $scope.editMode = 'addOutput';
                $('.recipeNode:not(".selected-node")').addClass('selected-node-selectable');
            }
        };

        $scope.removeDependency = function (depName) {
            var removedDeps = _.remove($scope.selectedJob.dependencies, function (dep) {
                return dep.name === depName;
            });
            console.log('removed ' + removedDeps.length + ' dependencies.');
            enableSaveRecipe();
            $scope.redraw();
        };

        $scope.removeInputMapping = function (depName, depOutput) {
            if( depName === 'recipe' ){
                // remove it from selectedJob.recipe_inputs
                var dep = _.remove($scope.selectedJob.recipe_inputs, { recipe_input: depOutput });
                enableSaveRecipe();
                $scope.redraw();
            } else {
                var dep = _.find($scope.selectedJob.dependencies, {name: depName});
                if (dep && dep.connections) {
                    // it's an input from another job
                    var removedCon = _.remove(dep.connections, function (conn) {
                        return conn.output === depOutput;
                    });
                    console.log('removed ' + removedCon.length + ' input connections.');
                    enableSaveRecipe();
                    $scope.redraw();
                }
            }

        };

        $scope.deleteRecipeJob = function(jobName){
            // remove dependent connections
            _.forEach($scope.recipeType.definition.jobs, function(job){
                _.remove(job.dependencies, {name: jobName});
            });
            // remove job from definition.jobs
            _.remove($scope.recipeType.definition.jobs, { name: jobName });
            // enable save and redraw
            $scope.selectedJob = null;
            enableSaveRecipe();
            $scope.redraw();
        };

        $scope.removeOutputMapping = function (jobName, depOutput) {
            // we have to remove output mapping from the job where the dependency is defined
            var receiver = _.find($scope.recipeType.definition.jobs,{name: jobName});
            // remove it from receiver.dependencies
            var dep = _.find(receiver.dependencies, {name: $scope.selectedJob.name});
            if (dep && dep.connections) {
                var removedCon = _.remove(dep.connections, function (conn) {
                    return conn.output === depOutput;
                });
                console.log('removed ' + removedCon.length + ' output connections.');
                enableSaveRecipe();
                $scope.redraw();
            }
        };

        $scope.selectItem = function(item){
            $scope.selectedItem = item;
        };

        $scope.$on('redrawRecipes', function () {
            $scope.redraw();
        });

        var addDependency = function(jobName){
            console.log($scope.selectedJob.name + '->' + jobName);
            if (!$scope.selectedJob.dependencies) {
                $scope.selectedJob.dependencies = [];
            }
            var existingDependency = _.find($scope.selectedJob.dependencies, {name: jobName});

            if(!existingDependency){ $scope.selectedJob.dependencies.push({name: jobName}); }
            $scope.selectedJob.depStart = false;
            $scope.editMode = '';
            $scope.dependencyBtnClass = 'fa-plus';

        };

        var getIoMappings = function () {
            if($scope.recipeType.definition){
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
                                _.forEach(job.recipe_inputs, function(recipeInput, key){
                                    if(recipeInput.job_input === jobInput.name){
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

            jobTypeService.getJobTypesOnce().then(function(data){
                $scope.jobTypeValues = data.results;
            });

            workspacesService.getWorkspaces().then(function(data){
                $scope.availableWorkspaces = data
            });

            $scope.$watch('recipeType', function (newValue, oldValue) {
                if ($scope.recipeType) {
                    if (!$scope.recipeType.id || $scope.recipeType.id === 0) {
                        $scope.mode = 'add';
                    }
                    _.forEach($scope.recipeType.definition.jobs, function (job, idx) {
                        if(!job.job_type.job_type_interface && $scope.recipeType.job_types){
                            var jobTypeData = _.find($scope.recipeType.job_types, {name: job.job_type.name, version: job.job_type.version});
                            $scope.recipeType.definition.jobs[idx].job_type = jobTypeData;
                        }

                    });

                    // setup string to bind comma delimited list of trigger rule configuration condition data types
                    if($scope.recipeType.trigger_rule && $scope.recipeType.trigger_rule.configuration && $scope.recipeType.trigger_rule.configuration.condition && $scope.recipeType.trigger_rule.configuration.condition.data_types){
                        $scope.recipeTypeTrigger.dataTypes = $scope.recipeType.trigger_rule.configuration.condition.data_types.join(',');
                    }

                    initGraph();
                    getIoMappings();
                    drawGraph($scope.isUpdate);
                }
            });
            if($rootScope.user){
                $scope.readonly = false;
            }
        };

        var initGraph = function () {
            // ******
            // setup D3 container and Graph
            // ******
            //$scope.selectedJob = null;
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
                inner.attr("transform", "translate(" + d3.event.translate + ")" +
                    "scale(" + d3.event.scale + ")");
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

        drawGraph = function (isUpdate) {
            // globals because dagre needs a reference to angular scope
            window.nodeClick = function(name) {
                var scope = angular.element(document.getElementById('recipeviewer')).scope();
                scope.$apply(function () {
                    scope.nodeClick(name);
                });
            };

            window.mapInput = function(jobName, jobOutput){
                var scope = angular.element(document.getElementById('recipeviewer')).scope();
                scope.$apply(function () {
                    scope.mapInput(jobName, jobOutput);
                });
            };

            $scope.isUpdate = true;
            if($scope.recipe){
                $scope.lastStatusChange = $scope.recipe.last_modified ? moment.duration(moment.utc($scope.recipe.last_modified).diff(moment.utc())).humanize(true) : '';
            }

            var jobs = [];
            if ($scope.recipeType.definition) {
                jobs = $scope.recipeType.definition.jobs;
            }
            var childCounts = [];
            // create graph objects
            for (var idx in jobs) {
                var job = jobs[idx];

                if ( job.dependencies === undefined || job.dependencies.length < 1) {
                    job.depStart = true;
                }
                var className = getRecipeTypeJobClassName(job);

                var html = '<div>';
                //var html = "<div onclick=\"console.log('" + job.job_type.name + "')\">";
                html += '<span class="status"></span>';
                //   html += "<span class=consumers>"+worker.consumers+"</span>";
                html += '<span class="name">';
                if (job.job_type) {
                    //console.log(job.jobType);
                    html += '<div id="' + job.name + '" class="recipeNode" onclick="nodeClick(\'' + job.name + '\')"><span class="name">' + job.job_type.getIcon() + ' ' + job.name + '</span></div>';
                    //if(jobType.name){
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
                label: '<div><span class=name>End</span></div>',
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

                // Zoom and scale to fit
                var zoomScale = zoom.scale();
                var graphWidth = graph.graph().width + 40;
                var graphHeight = graph.graph().height + 40;
                var width = parseInt(svg.style("width").replace(/px/, ""));
                var height = parseInt(svg.style("height").replace(/px/, ""));
                //zoomScale = Math.min(width / graphWidth, height / graphHeight);
                //if(zoomScale<0.80){
                //  zoomScale = 0.80;
                // }
                zoomScale = 0.75;
                if(zoomScale < 1){
                    //console.log('zoomScale: ' + zoomScale);
                    var translate = [0,0];// [(width*zoomScale)-(graphWidth*zoomScale), 0];
                    zoom.translate(translate);
                    zoom.scale(zoomScale);
                    zoom.event(isUpdate ? svg.transition().duration(500) : d3.select("svg"));
                }

                // add selected class to appropriate node
                if($scope.selectedJob){
                    $('#' + $scope.selectedJob.name).addClass('selected-node');
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
            templateUrl: 'modules/recipes/partials/recipeGraphViewerTemplate.html',
            restrict: 'E',
            scope: {
                recipeType: '=',
                recipe: '=',
                isModified: '=modified',
                allowEdit: '=',
                hasContainer: '='
            },
            link: function (scope) {
                angular.element(document).ready(function () {
                    var elHeight = document.getElementsByClassName('recipe-viewer-title')[0].scrollHeight;
                    scope.detailMaxHeight = scope.$parent.detailMaxHeight ? scope.$parent.detailMaxHeight - elHeight : 700;
                    scope.detailContainerStyle = 'height: ' + scope.detailMaxHeight + 'px; max-height: ' + scope.detailMaxHeight + 'px; overflow-y: auto;';
                });
            }
        };

    });
})();
