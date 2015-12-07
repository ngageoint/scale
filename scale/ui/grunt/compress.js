'use strict';

module.exports = function(grunt) {

    grunt.config('compress', {

        main: {
            options: {
                archive: 'dist/scale-ui.zip',
            },
            expand: true,
            cwd: 'dist',
            src: ['**/*'],
            dest: 'scale-ui/'
        }

    });

    grunt.loadNpmTasks('grunt-contrib-compress');
};
