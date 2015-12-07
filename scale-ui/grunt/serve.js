/**
 *
 */
'use strict';

module.exports = function(grunt) {

    grunt.config('connect', {
        // Default options for all tasks below
        options: {
            port: 9000,
            // Change this to '0.0.0.0' to access the server from outside.
            // hostname: 'localhost',
            hostname: '127.0.0.1',
            livereload: 35729,
            middleware: function(connect, options) {
                console.log("Options: " + JSON.stringify(options));
                var middlewares = [require('grunt-connect-proxy/lib/utils').proxyRequest];
                options.base.forEach(function(base) {
                    console.log('    static: ' + base);
                    middlewares.push(connect.static(base));
                });
                var directory = options.directory || options.base[options.base.length - 1];
                middlewares.push(connect.directory(directory));
                /*middlewares.unshift(function (req, res, next) {
                    if (req.url === '/test/data/v3/queueDepthCombined.json' || req.url === '/test/data/v3/jobTypes.json' || req.url === '/test/data/v3/jobTypeStats.json') {
                        res.statusCode = 503;
                    }
                    return next();
                });*/
                return middlewares;
            }
        },
        // If you want to pass through to the django server running at /api,
        // you also need to put the 'configureProxies:server' task right
        // before the 'connect:xxx' task.
        proxies: [{
            context: '/api',
            host: '127.0.0.1',
            port: 8000,
            https: false,
            changeOrigin: false,
            xforward: false
        }],
        // Connect/Serve Tasks here.
        livereload: {
            options: {
                open: true,
                base: [
                    'build',
                    'app'
                ]
            }
        },
        test: {
            options: {
                port: 9001,
                base: [
                    'build',
                    'test',
                    'app'
                ]
            }
        },
        dist: {
            options: {
                base: ['dist'],
                keepalive: true,
                open: true
            }
        }
    });

    grunt.config('watch', {
        js: {
            files: ['app/modules/**/*.js','app/modules/**/*.html','app/styles/**/*.less'],
            tasks: ['clean:dist', 'less:dist', 'copy:build'],
            options: {
                livereload: true
            }
        },
        json: {
            files: ['app/test/data/**/*.json'],
            tasks: ['clean:dist', 'copy:build'],
            options: {
                livereload: false
            }
        },
        livereload: {
            options: {
                livereload: '<%= connect.options.livereload %>'
            },
            files: [
                'app/**/*.html',
                'app/modules/**/*.js',
                'app/styles/**/*.less',
                'app/images/**/*'
            ]
        }
    });

    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-connect-proxy');
    grunt.loadNpmTasks('grunt-contrib-connect');
};
