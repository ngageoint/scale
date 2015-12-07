(function () {
    'use strict';

    angular.module('scaleApp').controller('feedDetailsController', function($scope, $location, scaleConfig, navService, subnavService, feedService) {
        $scope.loading = true;
        $scope.feedData = {};
        $scope.subnavLinks = scaleConfig.subnavLinks.feed;
        $scope.useIngestTime = 'false';

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
            if(strikeId != $location.search().strike_id){
                params.strike_id = strikeId;
            }
            else if($location.search().strike_id){
                params.strike_id = $location.search().strike_id;
            }
            var useIngestTime = $scope.useIngestTime ? $scope.useIngestTime : null;
            if(useIngestTime != $location.search().use_ingest_time){

               params.use_ingest_time = useIngestTime;
            }
            else if($location.search().use_ingest_time){
               console.log('getFeedParams use_ingest_time: ' + $location.search().use_ingest_time);
               params.use_ingest_time = $location.search().use_ingest_time;
            }
            return params;
        };

        var getFeed = function () {
            $scope.loading = true;
            if($location.search().use_ingest_time){
              $scope.useIngestTime = $location.search().use_ingest_time;
            }
            var feedParams = getFeedParams();
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
    });
})();
