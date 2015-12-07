/**
 * AutoPrefixer - Adds vender prefixes to CSS so you don't have to!
 */
'use strict';

module.exports = function(grunt) {

    grunt.config('autoprefixer', {
        options: {
            browsers: ['last 2 versions']
        },
        dist: {
            files: [{
                expand: true,
                cwd: 'app/styles/',
                src: '**/*.css',
                dest: 'app/styles/'
            }]
        }
    });

    grunt.loadNpmTasks('grunt-autoprefixer');
};
