'use strict';

module.exports = function(grunt) {

    grunt.config('file-creator', {

        version: {
            'dist/version.txt': function(fs, fd, done) {

                // os ships with node.js, exec-sync is in our package.json
                var os = require('os');
                var execSync = require('exec-sync');

                var buildtime = new Date();
                var hostname = os.hostname();
                var osType = os.type();
                var username = process.env['USER'];
                var dir = process.env['PWD'];

                // get current git revision from git.
                // Requires 'git' command line!!
                var rev = 'Not Available';
                try {
                    rev = execSync('git rev-parse HEAD');
                }
                catch (err) {
                    console.log('Error running "git rev-parse HEAD"');
                    console.log('    ' + err.message);
                }

                fs.writeSync(fd, '----------------\n');
                fs.writeSync(fd, 'Site Seer User Interface\n');
                fs.writeSync(fd, 'seer-ui.zip\n');
                fs.writeSync(fd, '----------------\n\n');

                fs.writeSync(fd, 'Git Revision: ' + rev + '\n');
                fs.writeSync(fd, 'Build Time: ' + buildtime + '\n');

                fs.writeSync(fd, 'Build Machine Information\n');
                fs.writeSync(fd, '    Host: ' + hostname + '\n');
                fs.writeSync(fd, '      OS: ' + osType + '\n');
                fs.writeSync(fd, '    User: ' + username + '\n');
                fs.writeSync(fd, '     Dir: ' + dir + '\n');
                fs.writeSync(fd, '\n\n');
                done();
            }
        }
    });

    grunt.loadNpmTasks('grunt-file-creator');
};
