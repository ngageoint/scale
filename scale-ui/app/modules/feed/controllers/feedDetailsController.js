(function () {
    'use strict';

    angular.module('scaleApp').controller('feedDetailsController', function ($scope, $location, scaleConfig, navService, subnavService, feedService, moment) {
        var vm = this;
        
        vm.loading = true;
        vm.feedData = {};
        vm.subnavLinks = scaleConfig.subnavLinks.feed;
        vm.useIngestTime = 'false';
        vm.filterValue = 1;
        vm.filterDuration = 'w';

        vm.changeFeedSelection = function (){
            setFeedUrl();
            //getFeed();
        };

        vm.changeIngestTimeSelection = function (){
            setFeedUrl();
            getFeed();
        };

        var getFeedParams = function (){
            var params = {};
            var strikeId = vm.selectedFeed ? vm.selectedFeed.strike.id : null;
            var useIngestTime = vm.useIngestTime ? vm.useIngestTime : null;

            params.started = moment.utc().subtract(vm.filterValue, vm.filterDuration).startOf('d').toISOString();
            params.ended = moment.utc(params.started).add(1, vm.filterDuration).endOf('d').toISOString();

            if (strikeId != $location.search().strike_id) {
                params.strike_id = strikeId;
            } else if ($location.search().strike_id) {
                params.strike_id = $location.search().strike_id;
            }

            if (useIngestTime != $location.search().use_ingest_time) {
               params.use_ingest_time = useIngestTime;
            } else if ($location.search().use_ingest_time) {
               console.log('getFeedParams use_ingest_time: ' + $location.search().use_ingest_time);
               params.use_ingest_time = $location.search().use_ingest_time;
            }

            return params;
        };

        var getFeed = function () {
            vm.loading = true;
            if ($location.search().use_ingest_time) {
                vm.useIngestTime = $location.search().use_ingest_time;
            }
            var feedParams = getFeedParams();
            $location.search(feedParams).replace();
            feedService.getFeed(feedParams).then(function (data) {
                vm.allFeeds = _.sortByOrder(data.results, ['strike.name'], ['asc']);
                var strikeId = $location.search().strike_id;
                if(strikeId){
                    // set selectedFeed = new feed
                    var feed = _.find(vm.allFeeds, function (feed){
                        return feed.strike.id == strikeId;
                    });
                    vm.selectedFeed = feed ? feed : null;
                } else {
                    vm.selectedFeed = vm.allFeeds[0];
                    setFeedUrl();
                }
            }).finally(function (){
                vm.loading = false;
            });
        };

        vm.updateFeedRange = function (action) {
            if (action === 'older') {
                vm.filterValue++;
            } else if (action === 'newer') {
                if (vm.filterValue > 1) {
                    vm.filterValue--;
                }
            } else if (action === 'today') {
                vm.filterValue = 1;
            }
            getFeed();
        };

        var setFeedUrl = function (){
            // set param in URL
            var params = getFeedParams();
            $location.search(params).replace();
        };

        var initialize = function () {
            navService.updateLocation('feed');
            subnavService.setCurrentPath('feed');
            getFeed();
        };

        initialize();

        $scope.$watch('vm.filterValue', function (value) {
            var $feedNewer = $('.feed-newer'),
                $feedToday = $('.feed-today');

            if (value > 1) {
                $feedNewer.removeAttr('disabled');
                $feedToday.removeAttr('disabled');
            } else {
                $feedNewer.attr('disabled', 'disabled');
                $feedToday.attr('disabled', 'disabled');
            }
        });
    });
})();
