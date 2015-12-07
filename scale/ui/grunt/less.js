'use strict';

module.exports = function(grunt) {

    grunt.config('less', {
      dist:{
          files: [
              {
                  // no need for files, the config below should work
                  expand: true,
                  cwd: 'app/styles',
                  src: ['*.less'],
                  dest: './app/styles/',
                  ext: '.css'
              },
              {
                  // no need for files, the config below should work
                  expand: true,
                  cwd: 'app/styles/components',
                  src: ['*.less'],
                  dest: './app/styles/components',
                  ext: '.css'
              },

              {
                  // no need for files, the config below should work
                  expand: true,
                  cwd: 'app/styles/pages',
                  src: ['*.less'],
                  dest: './app/styles/pages',
                  ext: '.css'
              }
          ]
      }
    });

    grunt.loadNpmTasks('grunt-contrib-less');
};
