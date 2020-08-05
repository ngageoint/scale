#!/usr/bin/env sh

API_TOKEN="fab1d1a2ace51f11ccb29246a3a1d99143908ceb"
CLUSTER="oarfish"

#+------------------------------------------------------
#|   NAME:         validateJSON()
#|   PARAMETERS:   url_snip, json_file   
#+------------------------------------------------------
validateJSON() {
    # Validate Workspace
    IS_VALID=$(curl -skLX POST \
    -H "Cookie: csrftoken=${CSRF_TOKEN}" \
    -H "Authorization: TOKEN ${API_TOKEN}" \
    -H "Content-Type: application/json" -T $2 \
    https://scale.oarfish.aisohio.net/api/v7/$1/validation)

    # Check for Validation
    if [ "${IS_VALID}" = '{"is_valid":true,"errors":[],"warnings":[]}' ]; then
        echo "LOG> $1 valid!"
        return 0
    elif [ "${IS_VALID}" = '{"diff":{},"is_valid":true,"errors":[],"warnings":[]}' ]; then
        echo "LOG> $1 valid and diff is empty!"
        return 0
    else
        echo ${IS_VALID}
        echo "LOG> $1 invalid!"
        exit 1
    fi
}

#+------------------------------------------------------
#|   NAME:         checkDuplicates()
#|   PARAMETERS:   variable_checked, parameter
#+------------------------------------------------------
checkDuplicates() {
    if [[ -n $1 ]]; then
        echo "Duplicate parameter \"$2\"" 
        exit 1
    fi
}

#+------------------------------------------------------
#|   NAME:         checkFile()
#|   PARAMETERS:   file_name
#+------------------------------------------------------
checkFile() {
    if [[ ! -f $1 ]]; then
        echo "\"$1\" doesn't exists"
        exit 2
    fi
}

# Replace equal sign format
set -- $(echo "$@" | sed 's/[=]/ /g')

# Argument Parsing
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -h|--help)
            echo "Usage: ./autodeploy.sh [options...]"
            echo "   -w, --workspace <file>    verifies and creates a workspace based on the json file provied"
            echo "   -j, --job-type <file>      verifies and creates a job type based on the json file provied"
            echo "   -r, --recipe-type <file>   verifies and creates a recipe type based on the json file provied"
            echo "   -s, --strike <file>        verifies and creates a strike based on the json file provied"
            echo 'Note: short fromat not supported (ex. % ./autodeploy.sh -wjrs)'
            exit 0;;
        -w|--workspace)
            checkDuplicates "${WORKSPACE}" "-w"
            shift
            checkFile "$1"
            WORKSPACE="$1";;
        -j|--job-type)
            checkDuplicates "${JOB_TYPE}" "-j"
            shift
            checkFile "$1"
            JOB_TYPE="$1";;
        -r|--recipe-type)
            checkDuplicates "${RECIPE_TYPE}" "-r"
            shift
            checkFile "$1"
            RECIPE_TYPE="$1";;
        -s|--strike)
            checkDuplicates "${STRIKE}" "-s"
            shift
            checkFile "$1"
            STRIKE="$1";;
        *) 
            echo "Unkown parameter passed: $1";;
    esac
    shift
done

# Get CSRF Token
CSRF_TOKEN=$(curl -skLX GET \
https://scale.${CLUSTER}.aisohio.net/api/admin --cookie-jar - \
| grep 'csrftoken' | sed 's/^.*csrftoken[[:space:]]]*//g')
echo "LOG> CSRF TOKEN: ${CSRF_TOKEN}"

# Workspace
if [[ -n ${WORKSPACE} ]]; then
    validateJSON "workspaces" ${WORKSPACE}



fi

    

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