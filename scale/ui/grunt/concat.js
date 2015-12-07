'use strict';

module.exports = function(grunt) {

    // Reads HTML for usemin blocks to enable smart builds that automatically
    // concat, minify and revision files. Creates configurations in memory so
    // additional tasks can operate on them

    grunt.config('useminPrepare', {
        html: 'app/index.html',
        options: {
            dest: 'build'
        }
    });

    grunt.config('usemin', {
        html: ['build/**/*.html'],
        css: ['build/styles/**/*.css'],
        options: {
            assetsDirs: ['build']
        }
    });

    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-usemin');
};
