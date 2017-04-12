
.. _algorithm_integration_step3:

Encapsulating your algorithm in a Docker container
==================================================

Once you have a completely standalone algorithm that generates a results manifest, you can begin to create your
Dockerfile which is a set of instructions on how to build your Docker container.

Docker containers can be built upon existing containers using the FROM command and comments can be added to the
dockerfile with the # symbol

Docker containers do not have access to files or NFS mounts on the host machine.

Docker containers in Scale have no knowledge of other containers running and cannot share resources or data across
containers.  However, the output of a container can be tied to the input of another container using recipes and the
outputs defined in the algorithm's results manifest file.

Once a container is destroyed, the files in the container no longer exist.

Docker containers should be as small as possible.  The Docker containers are pulled and cached on the host the first
time it is used and will update when the cache no longer matches the Docker registry.  Excessively large files will
unnecessarily fill up the host machine's disk space requiring the host machine's entire cache to be reset.

To build the Docker image, Docker must be installed on the system and the Docker daemon running. Depending on the
Linux system, the following packages will need to be installed:

1. docker-io and lxc for Centos6 
2. docker and lxc for Centos7

Next the Docker daemon service needs to be started

1. "systemctl enable docker" for Centos6
2. "systemctl start docker" command for Centos7

Example Dockerfile
^^^^^^^^^^^^^^^^^^

.. code-block:: bash
    :linenos:
    
    #Inherit from the centos 7 base image
    FROM centos:6
    
    #It is a good practice to set the version number and creator in the dockerfile
    ENV VERSION 1.0.0  
    MAINTAINER John_Doe
    
    #The RUN command will execute commands in the container
    RUN mkdir -p /app
    
    #The ADD command will copy both entire directories and single files. COPY only copies files and for this
    #use case is preferred. (see the Dockerfile best practices at https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices)
    ADD Code/ /app/Code
    COPY my_wrapper.sh /app/my_wrapper.sh
    
    #Multiple RUN commands can be chained together using back slashes and &&
    #It's a good idea to finish with a "yum clean all" on centos images as this will
    #remove repository cache files making your image smaller
    RUN yum install -y zip \
        && chmod 755 /app/my_algorithm.sav \
        && chmod 755 /app/my_wrapper.sh \
        && cd /app \
        && yum clean all

    #Environment variables can be set using the ENV command
    ENV DISPLAY $HOSTNAME:0.0
    
    #Create a virtual frame buffer for algorithms that need a display
    RUN Xvfb :0 -screen 0 1280x1024x24 -ac -terminate > /dev/null &

    #The WORKDIR command will set the working directory when starting a container
    WORKDIR /app

    #The ENTRYPOINT is the default command that is run when the container is started
    ENTRYPOINT [ "/app/my_wrapper.sh"]
    

Building a Docker container from the dockerfile
-----------------------------------------------

Within a single folder, you should have

1. Your Dockerfile
2. Your code/application executables, optionally in folders
3. Any configuration files

To build a Docker container, first change your current working directory to the directory containing your dockerfile.
Next, execute the following build statement from the command line:

.. code-block:: bash

    docker build -t hostname:port/algorithm_name:tag .
    
The command "docker build" will build a new image from the source code at the path, which in this case is ".", which
refers to the current working directory.  The argument flag "-t" allows the build to be tagged with a name.  The
hostname and port specify a local docker index for distribution to scale. If you intend to store your image in the main
docker hub on the internet, leave these off. The tag is useful for specifying a version of the algorithm.


Testing a built docker container
--------------------------------

If your Docker build command is successful, you can interact with your container inside its environment.  This is a
good way to test your container before pushing it to the Docker registry.  To test your container, you use the
"docker run" command:

.. code-block:: bash

    docker run -it --rm --privileged -v /host_folder:/docker_folder:rw --entrypoint="/bin/bash" --name myFirstDocker hostname:port/algorithm_name:tag
    
The "-it" flags specify interactive mode where the standard input will be kept open on the container even if it is not
attached to anything.

The "--rm" flag will remove the container after it exists. Otherwise the container and its filesystem changes will
persist.

The "--privileged" flag is optional and is only necessary if you are mounting an NFS container inside your wrapper.  

The "-v" flag will mount a volume from the host machine so that it will be available within the container.  This is
useful to mount a directory containing data for testing your algorithm and output results to another mounted volume to
be saved on the host machine.

If using the "-v" flag, first list the folder on your host machine you want to mount, then the folder in the Docker
container you want to mount to separated by a colon (:).  You can also optionally specify the mount as read-only (ro) or
read-write (rw) with another colon separator at the end of the mount.  Each additional mount requires another "-v" flag.

The "--entrypoint" argument specifies what to use as your ENTRYPOINT when starting the container, i.e. what command is
first run. This overrides the entrypoint specified in the Dockerfile. Using "/bin/bash" will put you at the command
prompt within the container when using docker run.

The "--name" argument will give a user-defined custom name to the container, otherwise it will be assigned an arbitrary name

The last argument to the "docker run" command should be the name of your container you created with the "docker build" command

Starting and stopping Docker containers (and other useful commands)
-------------------------------------------------------------------

To see a list of currently cached Docker containers on your host machine

.. code-block:: bash

    docker images
    
To see a list of currently running/stopped Docker containers on your host machine

.. code-block:: bash

    docker ps -a

To stop a running Docker container

.. code-block:: bash

    docker stop <container_name>
    
To start a stopped Docker container

.. code-block:: bash

    docker start <container_name>
    
To remove a stopped container

.. code-block:: bash

    docker rm <container_name>
    
To enter a currently running container and get a bash shell

.. code-block:: bash

    docker exec -it <container_name> bash
