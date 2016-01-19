var gulp = require('gulp'),
    concat = require('gulp-concat'),
    connect = require('gulp-connect'),
    mainBowerFiles = require('main-bower-files'),
    less = require('gulp-less'),
    jshint = require('gulp-jshint'),
    sourcemaps = require('gulp-sourcemaps'),
    del = require('del'),
    uglify = require('gulp-uglify'),
    cssnano = require('gulp-cssnano'),
    gulpFilter = require('gulp-filter'),
    ngAnnotate = require('gulp-ng-annotate'),
    tar = require('gulp-tar'),
    gzip = require('gulp-gzip'),
    p = require('./package.json');

var paths = {
    styles: ['./app/styles/**/*.less','!./app/styles/variables/bootstrap-overrides.less'],
    scripts: ['./app/modules/**/*.js', './app/scripts/**/*.js'],
    html: ['./app/modules/**/*.html'],
    images: ['./app/images/**/*'],
    fonts: ['./app/fonts/**/*'],
    testData: ['./app/test/data/**/*']
};

// clean
gulp.task('clean', function () {
    return del([
        './build/**/*'
    ]);
});

gulp.task('clean-dist', function () {
    return del([
        './dist/**/*'
    ]);
});

gulp.task('clean-tmp', ['vendor-build'], function () {
    return del([
        './.tmp'
    ]);
});

gulp.task('clean-scale', ['deploy-scale'], function () {
    del([
        './scale'
    ]);
});

// vendor scripts and css
gulp.task('bower', ['clean'], function () {
    var jsFilter = gulpFilter('*.js', {restore: true});
    var cssFilter = gulpFilter(['*.css','*.less'], {restore: true});
    var imageFilter = gulpFilter(['*.jpg','*.png'], {restore: true});

    return gulp.src(mainBowerFiles())
        // js
        .pipe(jsFilter)
        .pipe(sourcemaps.init())
        .pipe(concat('vendor.js'))
        .pipe(sourcemaps.write())
        .pipe(gulp.dest('./build/scripts'))
        .pipe(jsFilter.restore)

        // css
        .pipe(cssFilter)
        .pipe(less())
        .pipe(concat('bower.css'))
        .pipe(gulp.dest('./.tmp'))
        .pipe(cssFilter.restore)

        // images
        .pipe(imageFilter)
        .pipe(gulp.dest('./build/stylesheets/images'))
});

// handle bootstrap separately to facilitate bootstrap overrides
// copy bootstrap mixins
gulp.task('bootstrapMixins', ['bower'], function () {
    return gulp.src('./app/bower_components/bootstrap/less/mixins/*.less')
        .pipe(gulp.dest('./.tmp/bootstrap/mixins'));
});

// copy bootstrap less files
gulp.task('bootstrap', ['bootstrapMixins'], function () {
    return gulp.src('./app/bower_components/bootstrap/less/*.less')
        .pipe(gulp.dest('./.tmp/bootstrap'));
});

// concat bootstrap variables and custom bootstrap override variables
gulp.task('bootstrapVariables', ['bootstrap'], function () {
    return gulp.src(['./app/bower_components/bootstrap/less/variables.less','./app/less/variables/bootstrap-overrides.less'])
        .pipe(concat('variables.less'))
        .pipe(gulp.dest('./.tmp/bootstrap'));
});

// compile bootstrap less
gulp.task('compileBootstrap', ['bootstrapVariables'], function () {
    return gulp.src('./.tmp/bootstrap/bootstrap.less')
        .pipe(less())
        .pipe(gulp.dest('./.tmp'))
});

// concat bootstrap and other bower css
gulp.task('vendor', ['compileBootstrap'], function () {
    return gulp.src('./.tmp/*.css')
        .pipe(concat('vendor.css'))
        .pipe(gulp.dest('./build/stylesheets'));
});

// vendor fonts
gulp.task('fontawesome', ['clean'], function () {
    return gulp.src('./app/bower_components/font-awesome/fonts/**/*.{otf,eot,woff,woff2,svg,ttf}')
        .pipe(gulp.dest('./build/fonts'));
});

gulp.task('glyphicons', ['clean'], function () {
    return gulp.src('./app/bower_components/bootstrap/fonts/**/*.{otf,eot,woff,woff2,svg,ttf}')
        .pipe(gulp.dest('./build/fonts'));
});

gulp.task('ui-grid', ['clean'], function () {
    return gulp.src('./app/bower_components/angular-ui-grid/**/*.{otf,eot,woff,woff2,svg,ttf}')
        .pipe(gulp.dest('./build/stylesheets'));
})

gulp.task('vendor-fonts', ['fontawesome','glyphicons', 'ui-grid']);

gulp.task('vendor-build', ['vendor', 'vendor-fonts']);

// app
var appJs = function () {
    return gulp.src(paths.scripts)
        .pipe(sourcemaps.init())
        .pipe(concat('app.js'))
        .pipe(ngAnnotate({ single_quotes: true }))
        .pipe(sourcemaps.write())
        .pipe(connect.reload())
        .pipe(gulp.dest('./build/scripts'));
};
gulp.task('app-js', ['clean'], appJs);
gulp.task('app-js-watch', appJs);

var appHtml = function () {
    return gulp.src(paths.html)
        .pipe(connect.reload())
        .pipe(gulp.dest('./build/modules'));
};
gulp.task('app-html', ['clean'], appHtml);
gulp.task('app-html-watch', appHtml);

var appCss = function () {
    return gulp.src(paths.styles)
        .pipe(sourcemaps.init())
        .pipe(less())
        .pipe(concat('app.css'))
        .pipe(sourcemaps.write())
        .pipe(connect.reload())
        .pipe(gulp.dest('./build/stylesheets'));
};
gulp.task('app-css', ['clean'], appCss);
gulp.task('app-css-watch', appCss);

var appImages = function () {
    return gulp.src(paths.images)
        .pipe(gulp.dest('./build/images'));
};
gulp.task('app-images', ['clean'], appImages);

var appFonts = function () {
    return gulp.src(paths.fonts)
        .pipe(gulp.dest('./build/fonts'));
};
gulp.task('app-fonts', ['clean'], appFonts);

var appTestData = function () {
    return gulp.src(paths.testData)
        .pipe(gulp.dest('./build/test/data'));
};
gulp.task('app-test-data', ['clean'], appTestData);

gulp.task('app-build', ['app-js', 'app-html', 'app-css', 'app-images', 'app-fonts', 'app-test-data']);

// code linting
gulp.task('lint', function () {
    return gulp.src(paths.scripts)
        .pipe(jshint({ devel: true, debug: true }))
        .pipe(jshint.reporter('jshint-stylish'))
        .pipe(jshint.reporter('fail'));
});

// uglify
gulp.task('uglify-vendor-js', ['build', 'clean-dist'], function () {
    gulp.src('./build/scripts/vendor.js')
        .pipe(uglify())
        .pipe(gulp.dest('./build/scripts'));
});

gulp.task('uglify-app-js', ['build', 'clean-dist'], function () {
    gulp.src('./build/scripts/app.js')
        .pipe(uglify())
        .pipe(gulp.dest('./build/scripts'));
});

gulp.task('uglify-app-css', ['build', 'clean-dist'], function () {
    gulp.src('./build/stylesheets/style.css')
        .pipe(cssnano())
        .pipe(gulp.dest('./build/stylesheets'));
});
gulp.task('uglify', ['uglify-vendor-js', 'uglify-app-js', 'uglify-app-css']);

// dev server
gulp.task('connect', ['build'], function () {
    connect.server({
        port: 9000,
        root: 'build',
        livereload: true
    });
});

// watch files
gulp.task('watch', ['connect'], function () {
    gulp.watch(paths.html, ['app-html-watch']);
    //gulp.watch(paths.scripts, ['lint', 'app-js-watch']);
    gulp.watch(paths.scripts, ['app-js-watch']);
    gulp.watch(paths.styles, ['app-css-watch']);
});

// build
gulp.task('build', ['vendor-build', 'clean-tmp', 'app-build'], function () {
    return gulp.src('app/index.html')
        .pipe(gulp.dest('build'));
});

// dist
gulp.task('dist', ['build', 'uglify', 'clean-dist'], function () {
    return gulp.src('./build/**/*')
        .pipe(gulp.dest('dist'));
});

// deploy
gulp.task('deploy-scale', ['dist'], function () {
    return gulp.src('./dist/**/*')
        .pipe(gulp.dest('./scale')) // this will be the name of the directory inside the archive
        .pipe(tar('scale' + p.version + '.tar'))
        .pipe(gzip())
        .pipe(gulp.dest('./deploy'));
});

gulp.task('deploy', ['deploy-scale', 'clean-scale']);

// default gulp task
gulp.task('default', ['build', 'connect', 'watch']);
