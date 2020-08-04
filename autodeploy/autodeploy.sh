#!/usr/bin/env sh

# Arguments
WORKSPACE=$1
API_TOKEN="fab1d1a2ace51f11ccb29246a3a1d99143908ceb"
CLUSTER="oarfish"

# Get CSRF Token
CSRF_TOKEN=$(curl -skLX GET \
https://scale.${CLUSTER}.aisohio.net/api/admin --cookie-jar - \
| grep 'csrftoken' | sed 's/^.*csrftoken[[:space:]]]*//g')
echo "CSRF TOKEN: ${CSRF_TOKEN}"

# Validate Workspace
IS_VALID=$(curl -skLX POST \
-H "Cookie: csrftoken=${CSRF_TOKEN}" \
-H "Authorization: TOKEN ${API_TOKEN}" \
-H "Content-Type: application/json" -T ${WORKSPACE} \
https://scale.oarfish.aisohio.net/api/v7/workspaces/validation)

# Check for Validation
if [ "${IS_VALID}" = '{"is_valid":true,"errors":[],"warnings":[]}' ]; then
    echo "LOG> Workspace valid!"
elif [ "${IS_VALID}" = '{"detail":"Missing required parameter: \"configuration\""}' ]; then
    echo "LOG> Workspace invalid!"
    exit 1
else
    echo "LOG> Unkown error during workspace validation!"
    exit 2
fi

# Create Workspace
curl -skLX POST \
-H "Cookie: csrftoken=${CSRF_TOKEN}" \
-H "Authorization: TOKEN ${API_TOKEN}" \
-H "Content-Type: application/json" -T ${WORKSPACE} \
https://scale.oarfish.aisohio.net/api/v7/workspaces