#!/usr/bin/env sh

validateJSON() {
    # Parameters
    local url_snip=$1
    local json_file=$2

    # Validate Workspace
    IS_VALID=$(curl -skLX POST \
    -H "Cookie: csrftoken=${CSRF_TOKEN}" \
    -H "Authorization: TOKEN ${API_TOKEN}" \
    -H "Content-Type: application/json" -T $json_file \
    https://scale.oarfish.aisohio.net/api/v7/$url_snip/validation)

    # Check for Validation
    if [ "${IS_VALID}" = '{"is_valid":true,"errors":[],"warnings":[]}' ]; then
        echo "LOG> $url_snip valid!"
        return 0
    elif [ "${IS_VALID}" = '{"diff":{},"is_valid":true,"errors":[],"warnings":[]}' ]; then
        echo "LOG> $url_snip valid and diff is empty!"
        return 0
    else
        echo ${IS_VALID}
        echo "LOG> $url_snip invalid!"
        exit 1
    fi
}

# Arguments
WORKSPACE=$1
JOBTYPE=$2
RECIPETYPE=$3
STRIKE=$4
API_TOKEN="fab1d1a2ace51f11ccb29246a3a1d99143908ceb"
CLUSTER="oarfish"

# Get CSRF Token
CSRF_TOKEN=$(curl -skLX GET \
https://scale.${CLUSTER}.aisohio.net/api/admin --cookie-jar - \
| grep 'csrftoken' | sed 's/^.*csrftoken[[:space:]]]*//g')
echo "LOG> CSRF TOKEN: ${CSRF_TOKEN}"

# Validate 
validateJSON "workspaces" ${WORKSPACE}
validateJSON "job-types" ${JOBTYPE}
validateJSON "recipe-types" ${RECIPETYPE}
validateJSON "strikes" ${STRIKE}





# curl -skLX GET \
# -H "Cookie: csrftoken=${CSRF_TOKEN}" \
# -H "Authorization: TOKEN ${API_TOKEN}" \
# https://scale.oarfish.aisohio.net/api/v7/jobs



# Create Workspace
# curl -skLX POST \
# -H "Cookie: csrftoken=${CSRF_TOKEN}" \
# -H "Authorization: TOKEN ${API_TOKEN}" \
# -H "Content-Type: application/json" -T ${WORKSPACE} \
# https://scale.oarfish.aisohio.net/api/v7/workspaces