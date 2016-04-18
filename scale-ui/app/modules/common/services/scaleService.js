(function () {
    'use strict';

    angular.module('scaleApp').service('scaleService', function (scaleConfig) {
        function padWithZero (input, length) {
            // Cast input to string
            input = '' + input;

            var paddingSize = Math.max(0, length - input.length);
            return new Array(paddingSize > 0 ? paddingSize + 1 : 0).join('0') + input;
        }

        return {
            calculateFileSizeFromMib: function(num){
                if (num > 0) {
                    if (num < 1024) {
                        return num.toFixed(2) + ' MB';
                    }
                    if (num >= 1024 && num < 1024*1024) {
                        return (num/1024).toFixed(2) + ' GB';
                    }
                    return (num/1024/1024).toFixed(2) + ' TB';
                }
                return num;
            },
            calculateFileSizeFromBytes: function(num,decimals){
                // if(precision){
                //     // round num to specified precision
                //     num = Math.round(num/precision);
                // }
                if (num > 0) {
                    if (num < 1024) {
                        return num.toFixed(decimals) + ' Bytes';
                    }
                    if (num >= 1024 && num < 1024*1024) {
                        return (num/1024).toFixed(decimals) + ' KB';
                    }
                    if (num >= 1024*1024 && num < 1024*1024*1024) {
                        return (num/1024/1024).toFixed(decimals) + ' MB';
                    }
                    if (num >= 1024*1024*1024 && num < 1024*1024*1024*1024) {
                        return (num/1024/1024/1024).toFixed(decimals) + ' GB';
                    }
                    return (num/1024/1024/1024/1024).toFixed(decimals) + ' TB';
                }
                return num;
            },
            getViewportSize: function () {
                var w = window,
                    d = document,
                    e = d.documentElement,
                    g = document.body,
                    x = w.innerWidth || e.clientWidth || g.clientWidth,
                    y = w.innerHeight || e.clientHeight || g.clientHeight;

                return {
                    width: x,
                    height: y
                };
            },
            calculateDuration: function (start, stop) {
                var to = moment.utc(stop),
                    from = moment.utc(start),
                    diff = moment.utc(to).diff(moment.utc(from));

                var duration = moment.duration(diff);

                return padWithZero(duration.days(), 2) + 'd, ' + padWithZero(duration.hours(), 2) + 'h, ' + padWithZero(duration.minutes(), 2) + 'm, ' + padWithZero(duration.seconds(), 2) + 's';
            },
            getDayString: function(dayNumber){
                var dayArr = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
                return dayArr[dayNumber];
            },
            isIE: function () {
                var ua = window.navigator.userAgent,
                    oldIE = ua.indexOf('MSIE'),
                    newIE = ua.indexOf('Trident/');

                if ((oldIE > -1) || (newIE > -1)) {
                    return true;
                }
                return false;
            }
        }
    });
})();
