(function () {
    'use strict';

    angular.module('scaleApp').controller('feedDetailsController', function($scope, $location, scaleConfig, navService, subnavService, feedService, moment) {
        $scope.loading = true;
        $scope.feedData = {};
        $scope.subnavLinks = scaleConfig.subnavLinks.feed;
        $scope.useIngestTime = 'false';
        $scope.filterValue = 1;
        $scope.filterDuration = 'w';

        $scope.changeFeedSelection = function(){
            setFeedUrl();
            //getFeed();
        };

        $scope.changeIngestTimeSelection = function(){
            setFeedUrl();
            getFeed();
        };

        var getFeedParams = function(){
            var params = {};
            var strikeId = $scope.selectedFeed ? $scope.selectedFeed.strike.id : null;
            var useIngestTime = $scope.useIngestTime ? $scope.useIngestTime : null;

            params.started = moment.utc().subtract($scope.filterValue, $scope.filterDuration).startOf('d').toISOString();
            params.ended = moment.utc(params.started).add(1, $scope.filterDuration).endOf('d').toISOString();

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
            $scope.loading = true;
            if ($location.search().use_ingest_time) {
                $scope.useIngestTime = $location.search().use_ingest_time;
            }
            var feedParams = getFeedParams();
            $location.search(feedParams);
            feedService.getFeed(feedParams).then(function (data) {
                $scope.allFeeds = _.sortByOrder(data.results, ['strike.name'], ['asc']);
                var strikeId = $location.search().strike_id;
                if(strikeId){
                    // set selectedFeed = new feed
                    var feed = _.find($scope.allFeeds, function(feed){
                        return feed.strike.id == strikeId;
                    });
                    $scope.selectedFeed = feed ? feed : null;
                } else {
                    $scope.selectedFeed = $scope.allFeeds[0];
                    setFeedUrl();
                }
            }).finally(function(){
                $scope.loading = false;
            });
        };

        $scope.updateFeedRange = function (action) {
            if (action === 'older') {
                $scope.filterValue++;
            } else if (action === 'newer') {
                if ($scope.filterValue > 1) {
                    $scope.filterValue--;
                }
            } else if (action === 'today') {
                $scope.filterValue = 1;
            }
            getFeed();
        };

        var setFeedUrl = function(){
            // set param in URL
            var params = getFeedParams();
            $location.search(params);
        };

        var initialize = function () {
            navService.updateLocation('feed');
            subnavService.setCurrentPath('feed');
            getFeed();
        };

        initialize();

        $scope.$watch('filterValue', function (value) {
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
