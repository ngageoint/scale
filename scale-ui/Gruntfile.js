/**
 * Main Gruntfile for Scale User Interface
 *
 * For task-specific configs, look in /grunt
 */
'use strict';

module.exports = function(grunt) {

    // Time how long tasks take. Can help when optimizing build times
    require('time-grunt')(grunt);

    // Load tasks from grunt directory
    grunt.loadTasks('grunt');

    grunt.registerTask('serve', [
        'clean:dist',
        'less:dist',
        'copy:build',
        'configureProxies:server',
        'connect:livereload',
        'watch'
    ]);

    grunt.registerTask('preview', [
        'dist-prepare',
        'configureProxies:server',
        'connect:dist'
    ]);

    grunt.registerTask('dist', [
        'dist-prepare',
        'compress'
    ]);

    grunt.registerTask('ghdist', [
        'ghdist-prepare'
    ]);

    grunt.registerTask('dist-prepare', [
        'clean:dist',
        'copy:build',
        'less:dist',
        'autoprefixer',
        'useminPrepare',
        'usemin',
        'concat',
        'copy:dist'
        //'file-creator:version'
    ]);

    grunt.registerTask('ghdist-prepare', [
        'clean:gh',
        'copy:build',
        'less:dist',
        'autoprefixer',
        'useminPrepare',
        'usemin',
        'concat',
        'copy:ghdist'
    ]);
    // Default is to run serve task
    return grunt.registerTask('default', 'serve');
};
