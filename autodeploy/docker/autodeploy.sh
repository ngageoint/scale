#!/usr/bin/env sh

API_TOKEN='fab1d1a2ace51f11ccb29246a3a1d99143908ceb'
SILO_TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYWRtaW4iLCJ1c2VybmFtZSI6ImFkbWluIn0.OAK7h0FKjwpoarCJdiuQ9q2zKW7D4KiyseyQLwfO5A8'
CLUSTER="oarfish"

#+------------------------------------------------------
#|   NAME:         validateJSON()
#|   PARAMETERS:   url_snip, json_file   
#+------------------------------------------------------
validateJSON() {
    RESPONSE="$(curl -skLX POST \
    -H "Cookie: csrftoken=${CSRF_TOKEN}" \
    -H "Authorization: TOKEN ${API_TOKEN}" \
    -H "Content-Type: application/json" -T $2 \
    https://scale.${CLUSTER}.aisohio.net/api/v7/$1/validation)"
    if [[ $(echo "${RESPONSE}" | jq '.is_valid') = "true" ]]; then
        if [[ $(echo "${RESPONSE}" | jq '.diff | length') = 0 ]]; then
            echo "Autodeploy: $1: '$2' is valid"
        else
            echo "Autodeploy: $1: '$2' is valid with a diff"
            #echo "${RESPONSE}" | jq '.diff'
        fi
    else
        echo "Error: $1: '$2' is not valid"
        echo "${RESPONSE}" | jq '.'
        exit 1
    fi
}

#+------------------------------------------------------
#|   NAME:         postJSON()
#|   PARAMETERS:   url_snip, json_file   
#+------------------------------------------------------
postJSON() {
    RESPONSE=$(curl -skLX GET \
    -H "Cookie: csrftoken=${CSRF_TOKEN}" \
    -H "Authorization: TOKEN ${API_TOKEN}" \
    https://scale.${CLUSTER}.aisohio.net/api/v7/$1)

    case $1 in
        workspaces|recipe-types|strikes)
            NAME=$(jq '.name' $2);;
        job-types)
            NAME=$(jq '.manifest.job.name' $2)
            VERSION=$(jq '.manifest.job.jobVersion' $2);;
    esac

    if [[ $(echo "${RESPONSE}" | jq "has(\"results\")") = "true" ]]; then
        if [[ $(echo "${RESPONSE}" | jq ".results[] | select(.name == "${NAME}") | has(\"id\")") = "true" ]]; then
            echo "Autodeploy: $1: '$2' is a duplicate"
            case $1 in 
                workspaces|strikes)
                    ID=$(echo "${RESPONSE}" | jq ".results[] | select(.name == "${NAME}") | .id")
                    URL=$(echo "https://scale.${CLUSTER}.aisohio.net/api/v7/$1/${ID}" | sed 's/"//g');;
                job-types)
                    URL=$(echo "https://scale.${CLUSTER}.aisohio.net/api/v7/$1/${NAME}/${VERSION}" | sed 's/"//g');;
                recipe-types)
                    URL=$(echo "https://scale.${CLUSTER}.aisohio.net/api/v7/$1/${NAME}" | sed 's/"//g');;
            esac

            RESPONSE=$(curl -skLX PATCH \
            -H "Cookie: csrftoken=${CSRF_TOKEN}" \
            -H "Authorization: TOKEN ${API_TOKEN}" \
            -H "Content-Type: application/json" -T $2 \
            ${URL})
            if [[ $(echo "${RESPONSE}" | jq '.is_valid') != "true" ]]; then
                if [ "${RESPONSE}" != "" ]; then
                    echo "Error: $1: '$2' was not able to PATCH"
                    echo "${RESPONSE}"
                    exit 1
                fi
            fi
            echo "Autodeploy: $1: '$2' PATCH was successful"
            RESPONSE=$(curl -skLX GET \
            -H "Cookie: csrftoken=${CSRF_TOKEN}" \
            -H "Authorization: TOKEN ${API_TOKEN}" \
            ${URL})
        else
            echo "Autodeploy: $1: '$2' is original"
            RESPONSE=$(curl -skLX POST \
            -H "Cookie: csrftoken=${CSRF_TOKEN}" \
            -H "Authorization: TOKEN ${API_TOKEN}" \
            -H "Content-Type: application/json" -T $2 \
            https://scale.${CLUSTER}.aisohio.net/api/v7/$1)
            if [[ ! $(echo "${RESPONSE}" | jq 'has("id","name")') =~ "false" ]]; then
                echo "Autodeploy: $1: '$2' POST was successful"
            else
                echo "Error: $1: '$2' was not able to POST"
                echo "${RESPONSE}" | jq '.'
                exit 1
            fi
        fi
    else
        echo "Error: $1: Response expected 'results[]'"
        echo "${RESPONSE}"
        exit 1
    fi
}

#+------------------------------------------------------
#|   NAME:         checkDuplicates()
#|   PARAMETERS:   variable_checked, parameter
#+------------------------------------------------------
checkDuplicates() {
    if [[ -n $1 ]]; then
        echo "Error: '$2' is a duplicate"
        echo "Note: './autodeploy.sh --help' or './autodeploy.sh -h' for more information" 
        exit 1
    fi
}

#+------------------------------------------------------
#|   NAME:         checkFile()
#|   PARAMETERS:   file_name
#+------------------------------------------------------
checkFile() {
    if [[ ! -f $1 ]]; then
        echo "Error: '$1' doesn't exists"
        echo "Usage: ./autodeploy.sh $2 <file>"
        exit 1
    fi
}

# Replace equal sign format
set -- $(echo "$@" | sed 's/[=]/ /g')

# Argument Parsing
if [ $# == 0 ]; then
    echo "Usage: ./autodeploy.sh [options...]"
    echo "Note: './autodeploy.sh --help' or './autodeploy.sh -h' for more information"
    exit 0
fi

while [[ "$#" -gt 0 ]]; do
    OPTION=$1
    case $1 in
        -a|--api-token)
            checkDuplicates "${WORKSPACE}" "$1"
            shift
            API_TOKEN=$1
            echo "Autodeploy: api-token: '${API_TOKEN}'";;
        -h|--help)
            echo "Usage: ./autodeploy.sh [options...]"
            echo "   -a  --api-token <token>    replace the default api token"
            echo "   -w, --workspace <file>     verifies and creates a workspace based on the json file provied"
            echo "   -j, --job-type <file>      verifies and creates a job type based on the json file provied"
            echo "   -r, --recipe-type <file>   verifies and creates a recipe type based on the json file provied"
            echo "   -s, --strike <file>        verifies and creates a strike based on the json file provied"
            echo "       --silo                 scans registries to update images"
            echo "Note: short fromat not supported (ex. './autodeploy.sh -wjrs')"
            exit 0;;
        -w|--workspace)
            checkDuplicates "${WORKSPACE}" "$1"
            shift
            checkFile "$1" "${OPTION}"
            WORKSPACE="$1";;
        -j|--job-type)
            checkDuplicates "${JOB_TYPE}" "$1"
            shift
            checkFile "$1" "${OPTION}"
            JOB_TYPE="$1";;
        -r|--recipe-type)
            checkDuplicates "${RECIPE_TYPE}" "$1"
            shift
            checkFile "$1" "${OPTION}"
            RECIPE_TYPE="$1";;
        -s|--strike)
            checkDuplicates "${STRIKE}" "$1"
            shift
            checkFile "$1" "${OPTION}"
            STRIKE="$1";;
        --silo)
            checkDuplicates "${SILO}" "$1"
            SILO="true";;
        *) 
            echo "Unkown parameter passed: $1"
            exit 1;;
    esac
    shift
done

# SILO
if [[ -n ${SILO} ]]; then
    echo "Autodeploy: silo: scanning registries..."
    curl -sk \
    -H "Authorization: Token ${SILO_TOKEN}" \
    -H "Content-Type: application/json" \
    https://scale-silo.${CLUSTER}.aisohio.net/registries/scan
fi

# Get CSRF Token
CSRF_TOKEN=$(curl -skLX GET \
https://scale.${CLUSTER}.aisohio.net/api/admin --cookie-jar - \
| grep 'csrftoken' | sed 's/^.*csrftoken[[:space:]]]*//g' )
echo "Autodeploy: csrf-token: '${CSRF_TOKEN}'"

# Workspace
if [[ -n ${WORKSPACE} ]]; then
    validateJSON "workspaces" ${WORKSPACE}
    postJSON "workspaces" ${WORKSPACE}

    # Add Workspace Name to Job-type
    if [[ -n ${JOB_TYPE} ]]; then
        NAME_WORKSPACE="$(echo ${RESPONSE} | jq '.name')"
        JOB_TYPE_EDIT="$(jq ".configuration.output_workspaces.default=${NAME_WORKSPACE}" ${JOB_TYPE})" && \
        echo "${JOB_TYPE_EDIT}" > "${JOB_TYPE}"
        echo "Autodeploy: job-types: '${JOB_TYPE}' workspace updated to ${NAME_WORKSPACE}"
    fi

    # Add Workspace Name to Strike
    if [[ -n ${STRIKE} ]]; then
        NAME_WORKSPACE="$(echo ${RESPONSE} | jq '.name')"
        STRIKE_EDIT="$(jq ".configuration.workspace=${NAME_WORKSPACE}" ${STRIKE})" && \
        echo "${STRIKE_EDIT}" > "${STRIKE}"
        echo "Autodeploy: strikes: '${STRIKE}' workspace updated to ${NAME_WORKSPACE}"
    fi
fi

# Job-Type
if [[ -n ${JOB_TYPE} ]]; then
    validateJSON 'job-types' "${JOB_TYPE}"
    postJSON 'job-types' "${JOB_TYPE}"

    # Add Job-Type to Recipe-type
    if [[ -n ${RECIPE_TYPE} ]]; then
        JOB_TYPE_JSON="$(echo ${RESPONSE} | jq '.')"
        RECIPE_TYPE_EDIT="$(jq ".job_types=${JOB_TYPE_JSON}" ${RECIPE_TYPE})" && \
        echo "${RECIPE_TYPE_EDIT}" > "${RECIPE_TYPE}"
        echo "Autodeploy: recipe-types: '${RECIPE_TYPE}' job-type updated to $(echo ${JOB_TYPE_JSON} | jq '.name')"
    fi
    
fi

# Recipe-Type
if [[ -n ${RECIPE_TYPE} ]]; then
    validateJSON "recipe-types" ${RECIPE_TYPE}
    postJSON 'recipe-types' "${RECIPE_TYPE}"

    # Add Recipe Name to strike
    if [[ -n ${STRIKE} ]]; then
        NAME_RECIPE="$(echo ${RESPONSE} | jq '.name')"
        STRIKE_EDIT="$(jq ".configuration.recipe.name=${NAME_RECIPE}" ${STRIKE})" && \
        echo "${STRIKE_EDIT}" > "${STRIKE}"
        echo "Autodeploy: strikes: '${STRIKE}' recipe updated to ${NAME_RECIPE}"
    fi
fi

# Strike
if [[ -n ${STRIKE} ]]; then
    validateJSON "strikes" "${STRIKE}"
    postJSON 'strikes' "${STRIKE}"
fi