This contains DC/OS configuration files. These are stored here to easily associate a
version with the corresponding Scale version. You won't be able to use this directory
directly as a package repo for DC/OS. Instead, you'll need to clone and setup
the DC/OS universe and add a Scale entry with these files. You'll need to update the
Scale image ID (in the marathon and resource files) to correspond to the image ID for the
Scale Docker image.
