'use strict';

module.exports = function(grunt) {
    grunt.config('copy', {
        build: {
            files: [{
                // Everything in the app directory
                expand: true,
                cwd: 'app/',
                src: ['**'],
                dest: 'build/'
            }]
        },
        // copy files for distribution
        dist: {
            files: [{
                // Everything in the build directory
                expand: true,
                cwd: 'build/',
                src: ['**/*.html','**/*.png','**/*.ttf','**/*.woff','./test/data/v3/*.json'],
                dest: 'dist/'
            }, {
                // Get bootstrap theme map
                expand: true,
                cwd: 'build/bower_components/bootstrap/dist/css/',
                src: ['bootstrap-theme-map.css.map'],
                dest: 'dist/styles'
            }, {
                // Get toastr map
                expand: true,
                cwd: 'build/bower_components/toastr/',
                src: ['toastr.js.map'],
                dest: 'dist/scripts'
            }, {
                // Get Bootstrap fonts (glyphicons)
                expand: true,
                cwd: 'build/bower_components/bootstrap/fonts/',
                src: ['**'],
                dest: 'dist/fonts/'
            }, {
                // Get Font Awesome fonts
                expand: true,
                cwd: 'build/bower_components/font-awesome/fonts/',
                src: ['**'],
                dest: 'dist/fonts/'
            }, {
                // Get Angular UI Grid fonts
                expand: true,
                cwd: 'build/bower_components/angular-ui-grid/',
                src: ['**/*.ttf', '**/*.woff'],
                dest: 'dist/styles/'
            }, {
                // Concatenated CSS
                expand: true,
                cwd: '.tmp/concat/styles/',
                src: ['**'],
                dest: 'dist/styles/'
            }, {
                // Concatenated JS
                expand: true,
                cwd: '.tmp/concat/scripts/',
                src: ['**/*.js'],
                dest: 'dist/scripts/'
            }, {
                // scaleConfig JS
                expand: true,
                cwd: 'build/modules/',
                src: ['scaleConfig.js'],
                dest: 'dist/modules/'
            }]
        },
        ghdist: {
            files: [{
                // Everything in the build directory
                expand: true,
                cwd: 'build/',
                src: ['**/*.html','**/*.png','**/*.ttf','**/*.woff','./test/data/v3/*.json'],
                dest: 'ghdist/'
            }, {
                // Get bootstrap theme map
                expand: true,
                cwd: 'build/bower_components/bootstrap/dist/css/',
                src: ['bootstrap-theme-map.css.map'],
                dest: 'ghdist/styles'
            }, {
                // Get toastr map
                expand: true,
                cwd: 'build/bower_components/toastr/',
                src: ['toastr.js.map'],
                dest: 'ghdist/scripts'
            }, {
                // Get Bootstrap fonts (glyphicons)
                expand: true,
                cwd: 'build/bower_components/bootstrap/fonts/',
                src: ['**'],
                dest: 'ghdist/fonts/'
            }, {
                // Get Font Awesome fonts
                expand: true,
                cwd: 'build/bower_components/font-awesome/fonts/',
                src: ['**'],
                dest: 'ghdist/fonts/'
            }, {
                // Get Angular UI Grid fonts
                expand: true,
                cwd: 'build/bower_components/angular-ui-grid/',
                src: ['**/*.ttf', '**/*.woff'],
                dest: 'ghdist/styles/'
            }, {
                // Concatenated CSS
                expand: true,
                cwd: '.tmp/concat/styles/',
                src: ['**'],
                dest: 'ghdist/styles/'
            }, {
                // Concatenated JS
                expand: true,
                cwd: '.tmp/concat/scripts/',
                src: ['**/*.js'],
                dest: 'ghdist/scripts/'
            }, {
                // scaleConfig JS
                expand: true,
                cwd: 'build/modules/',
                src: ['scaleConfig.js'],
                dest: 'ghdist/modules/'
            }, {
                // scaleConfigLocal JS
                expand: true,
                cwd: 'ghconfig',
                src: ['scaleConfig.local.js'],
                dest: 'ghdist/modules/'
            }]
        }
    });

    grunt.loadNpmTasks('grunt-contrib-copy');
};
