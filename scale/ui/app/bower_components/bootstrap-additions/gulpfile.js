'use strict';

var gulp = require('gulp');
var config = require('ng-factory').use(gulp, {
  paths: {
    styles: '**/*.less'
  },
  bower: {
    exclude: /jquery|js\/bootstrap|\.less/
  }
});

//
// Tasks

gulp.task('serve', gulp.series('ng:serve'));

var del = require('del');
var path = require('path');
gulp.task('build', gulp.series('ng:build', function afterBuild(done) {
  var paths = config.paths;
  // Delete useless module.* build files
  // del(path.join(paths.dest, 'module.*'), done);
}));

gulp.task('pages', gulp.series('ng:pages', function afterPages(done) {
  var paths = config.docs;
  return gulp.src(['bower_components/highlightjs/styles/github.css'], {cwd: paths.cwd, base: paths.cwd})
    .pipe(gulp.dest(paths.dest));
}));
