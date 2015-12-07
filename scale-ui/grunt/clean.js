/**
 * Clean tasks - remove build/tmp artifacts
 */
'use strict';

module.exports = function(grunt) {

    grunt.config('clean', {
        dist: {
            files: [{
                dot: true,
                src: [
                    '.tmp',
                    'build',
                    'dist/*'
                ]
            }],
            options: {
                force: true
            }
        },
        gh: {
            files: [{
                dot: true,
                src: [
                    '.tmp',
                    'build',
                    'ghdist/*'
                ]
            }],
            options: {
                force: true
            }
        }
    });

    grunt.loadNpmTasks('grunt-contrib-clean');
};
