#!/usr/bin/env sh

args=$@
ARGS_ARRAY=$(echo ${args} | sed 's/[=]/ /g')

for i in ${ARGS_ARRAY}; do
    echo ${ARGS_ARRAY}
    case $i in
        -h|--help)
            echo "Workspace parameter passed: $i"
            exit 0;;
        -w|--workspace)
            echo "Workspace parameter passed: $i"
            exit 0;;
        *) 
            echo "Unkown parameter passed: $i"
            exit 1;;
    esac
    shift
done
    

# while [[ "$#" -gt 0 ]]; do
#     case $1 in
#         -d|--deploy) deploy="$2"; shift ;;
#         -u|--uglify) uglify=1 ;;
#         *) echo "Unknown parameter passed: $1"; exit 1 ;;
#     esac
#     shift
# done

# for i in "$@"
# do
# case $i in
#     -e=*|--extension=*)
#     EXTENSION="${i#*=}"
#     shift # past argument=value
#     ;;
#     -s=*|--searchpath=*)
#     SEARCHPATH="${i#*=}"
#     shift # past argument=value
#     ;;
#     -l=*|--lib=*)
#     LIBPATH="${i#*=}"
#     shift # past argument=value
#     ;;
#     --default)
#     DEFAULT=YES
#     shift # past argument with no value
#     ;;
#     *)
#           # unknown option
#     ;;
# esac
# done