# Scale UI
Web application front-end for the Scale data processing system.

## Usage

The Scale UI uses Bower and NPM for package management. Gulp is used as the task runner.
The following commands will get you up and running a local server from a fresh clone:

```
npm install -g gulp
npm install
gulp
```

Packaging of a UI tarball for release apart from Docker can be accomplished using the `deploy` task:

```
gulp deploy
```

## Dependencies
When updating either the Bower or NPM dependencies the tarball containing all the dependencies should be updated.
This is critical for persisting into the Docker image. Tarballs are used as a means to minimize the context size passed
to the Docker daemon on build. The tarballs can be updated for Bower and NPM as shown below:

```
tar cvzf bower_components.tar.gz app/bower_components
tar cvzf node_modules.tar.gz node_modules
```

These tarballs should also be committed and pushed to the remote repository.


## Analytics
For integration with your analytics platform, create a file named analytics.html
containing your tracking code (google analytics, piwik, etc...) and put it in
the config directory before executing ```gulp deploy```. 
