'use strict';

module.exports = function(grunt) {

    var revFiles = [
//        'dist/modules/**/*.js',
//        'dist/modules/**/*.html',
//        'dist/scripts/*.js',
        'dist/styles/*.css'
    ];

    grunt.config('filerev', {
        options: {
            encoding: 'utf8',
            algorithm: 'md5',
            length: 6
        },
        assets: {
            src: revFiles
        }
    });

    grunt.config('userev', {
        assets: {
            src: revFiles
        },
        index: {
            src: 'dist/scale-ui/index.html'
        }
    });

    grunt.loadNpmTasks('grunt-filerev');
    grunt.loadNpmTasks('grunt-userev');
};
