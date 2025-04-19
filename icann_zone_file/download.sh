#!/bin/bash
################################################################################
# download.sh
################################################################################

#===========================================================
# Options
#===========================================================
USERNAME="$1"
PASSWORD="$2"
TLDZONE="$3"
TARGET_PATH="$4"

if [[ "${USERNAME}" == "" || "${PASSWORD}" == "" || "${TLDZONE}" == "" || "${TARGET_PATH}" == "" || ! -d "${TARGET_PATH}" ]]
then
echo "Usage: download.sh USERNAME PASSWORD TLDZONE TARGET_PATH"
echo "TLDZONE: com.zone, org.zone, net.zone"
exit 1
fi

#===========================================================
# Configuration
#===========================================================
THREADMAX="8"
CURLRETRY="3"
CHUNKSIZE="100000000"

#===========================================================
# AUTHENTICATION
#===========================================================
AUTHENTICATION_JSON=$(
    curl \
        --request POST \
        --header "Accept: application/json" \
        --header "Content-Type: application/json" \
        --data "{\"username\": \"${USERNAME}\", \"password\": \"$PASSWORD\"}" \
        https://account-api.icann.org/api/authenticate)
RESULT="${?}"
echo "AUTHENTICATION_JSON: ${AUTHENTICATION_JSON}"
if [[ "${RESULT}" != "0" ]]
then
    echo "Unexpected error: ${RESULT}"
    exit 1
fi

ACCESSTOKEN=$(echo "${AUTHENTICATION_JSON}" | jq --raw-output ".accessToken")
echo "ACCESSTOKEN: ${ACCESSTOKEN}"

#===========================================================
# LINKS
#===========================================================
LINKS_JSON=$(
    curl \
        --request GET \
        --header "Accept: application/json" \
        --header "Content-Type: application/json" \
        --header "Authorization: Bearer ${ACCESSTOKEN}" \
        https://czds-api.icann.org/czds/downloads/links)
RESULT="${?}"
echo "LINKS_JSON: ${LINKS_JSON}"
if [[ "${RESULT}" != "0" ]]
then
    echo "Unexpected error: ${RESULT}"
    exit 1
fi

for LINK in $(echo "${LINKS_JSON}" | jq --raw-output ".[]")
do
    LINKBASENAME=$(basename "${LINK}")
    if [[ "${LINKBASENAME}" == "${TLDZONE}" ]]
    then
        TLDZONELINK="${LINK}"
    fi
done
echo "TLDZONELINK: ${TLDZONELINK}"

#===========================================================
# STATUS
#===========================================================
STATUS_HEADERS=$(
    curl \
        --head \
        --header "Authorization: Bearer ${ACCESSTOKEN}" \
        "${TLDZONELINK}" | sed --expression "s/\r//g")
RESULT="${?}"
echo "STATUS_HEADERS: ${STATUS_HEADERS}"
if [[ "${RESULT}" != "0" ]]
then
    echo "Unexpected error: ${RESULT}"
    exit 1
fi

STATUS_CONTENTLENGTH=$(echo "${STATUS_HEADERS}" | grep "^Content-Length:" | sed --expression "s/^.*: //")
echo "STATUS_CONTENTLENGTH: ${STATUS_CONTENTLENGTH}"

STATUS_CONTENTLENGTHWIDTH="${#STATUS_CONTENTLENGTH}"
echo "STATUS_CONTENTLENGTHWIDTH: ${STATUS_CONTENTLENGTHWIDTH}"

STATUS_LASTMODIFIED=$(echo "${STATUS_HEADERS}" | grep "^Last-Modified:" | sed --expression "s/^.*: //")
echo "STATUS_LASTMODIFIED: ${STATUS_LASTMODIFIED}"

ISODATE=$(date --iso-8601=date --date="${STATUS_LASTMODIFIED}")
echo "ISODATE: ${ISODATE}"

TARGET_FILE_NAME="${TLDZONE}_${ISODATE}.txt.gz"
TARGET_PATH_FILE="${TARGET_PATH_FILE}/${TLDZONE}_${ISODATE}.txt.gz"

if [[ -f "${TARGET_PATH_FILE}" ]]
then
    echo "EXISTS: ${TARGET_FILE_NAME}"
    echo "No download needed."
    exit 1
fi

#===========================================================
# DOWNLOAD
#===========================================================
declare -a LABELS
declare -A LABEL_TO_START
declare -A LABEL_TO_END
declare -A LABEL_TO_SIZE
declare -A LABEL_TO_PATH_FILE
declare -A LABEL_TO_LOG_PATH_FILE
# STATUS: WAIT, DONE, <PID>
declare -A LABEL_TO_STATUS

# Prepare.
INDEX="1"
POS="0"
while [[ "${POS}" -lt "${STATUS_CONTENTLENGTH}" ]]
do
    let "START=${POS}"
    let "END=${POS}+${CHUNKSIZE}-1"
    if [[ "${END}" -ge "${STATUS_CONTENTLENGTH}" ]]
    then
        let "END=${STATUS_CONTENTLENGTH}-1"
    fi
    let "SIZE=${END}-${START}+1"
    printf -v INDEXPADDING "%03d" "${INDEX}"
    printf -v STARTPADDING "%0${#STATUS_CONTENTLENGTH}d" "${START}"
    printf -v ENDPADDING "%0${#STATUS_CONTENTLENGTH}d" "${END}"
    printf -v SIZEPADDING "%0${#CHUNKSIZE}d" "${SIZE}"
    LABEL="${TLDZONE}_${ISODATE}_${INDEXPADDING}_${STARTPADDING}_${ENDPADDING}_${SIZEPADDING}"
    LABELS["${INDEX}"]="${LABEL}"
    LABEL_TO_START["${LABEL}"]="${START}"
    LABEL_TO_END["${LABEL}"]="${END}"
    LABEL_TO_SIZE["${LABEL}"]="${SIZE}"
    LABEL_TO_PATH_FILE["${LABEL}"]="${TARGET_PATH}/${LABEL}"
    LABEL_TO_LOG_PATH_FILE["${LABEL}"]="${TARGET_PATH}/${LABEL}.log.txt"
    let "POS=${END}+1"
    let "INDEX=${INDEX}+1"
done

# Check.
CORRUPT="FALSE"
for LABEL in "${LABELS[@]}"
do
    if [[ -f "${LABEL_TO_PATH_FILE[${LABEL}]}" ]]
    then
        SIZE="${LABEL_TO_SIZE[${LABEL}]}"
        ACTUAL_SIZE=$(stat --format "%s" "${LABEL_TO_PATH_FILE[${LABEL}]}")
        if [[ "${ACTUAL_SIZE}" != "${SIZE}" ]]
        then
            echo "CORRUPT: ${LABEL_TO_PATH_FILE[${LABEL}]} (unexpected size: ${ACTUAL_SIZE})"
            CORRUPT="TRUE"
        fi
    fi
done
if [[ "${CORRUPT}" == "TRUE" ]]
then
    exit
fi

# Existing.
for LABEL in "${LABELS[@]}"
do
    if [[ -f "${LABEL_TO_PATH_FILE[${LABEL}]}" ]]
    then
        LABEL_TO_STATUS["${LABEL}"]="DONE"
    else
        LABEL_TO_STATUS["${LABEL}"]="WAIT"
    fi
    echo "${LABEL}: ${LABEL_TO_STATUS[${LABEL}]}"
done

# Download.
COMPLETE="FALSE"
while [[ "${COMPLETE}" == "FALSE" ]]
do
    # Update.
    COMPLETE="TRUE"
    LABEL_WAIT="FALSE"
    RUNTOTAL="0"
    for LABEL in "${LABELS[@]}"
    do
        STATUS="${LABEL_TO_STATUS[${LABEL}]}"
        if [[ "${STATUS}" == "WAIT" ]]
        then
            if [[ "${LABEL_WAIT}" == "FALSE" ]]
            then
                LABEL_WAIT="${LABEL}"
            fi
            COMPLETE="FALSE"
        else
            if [[ "${STATUS}" != "DONE" ]]
            then
                COMMAND=$(ps -p "${STATUS}" -o "comm=")
                if [[ "${COMMAND}" != "curl" ]]
                then
                    LABEL_TO_STATUS[${LABEL}]="DONE"
                    echo "${LABEL}: ${LABEL_TO_STATUS[${LABEL}]}"
                else
                    COMPLETE="FALSE"
                    let "RUNTOTAL=${RUNTOTAL}+1"
                fi
            fi
        fi
    done

    # Act.
    if [[ "${COMPLETE}" == "FALSE" ]]
    then
        if [[ "${LABEL_WAIT}" != "FALSE" ]]
        then
            if [[ "${RUNTOTAL}" -lt "${THREADMAX}" ]]
            then
                START="${LABEL_TO_START[${LABEL_WAIT}]}"
                END="${LABEL_TO_END[${LABEL_WAIT}]}"
                LABEL_LOG_PATH_FILE="${TARGET_PATH}/${LABEL_WAIT}.log.txt"
                curl \
                    --no-progress-meter \
                    --retry "${CURLRETRY}" \
                    --request GET \
                    --header "Authorization: Bearer ${ACCESSTOKEN}" \
                    --range "${START}-${END}" \
                    --stderr "${LABEL_TO_LOG_PATH_FILE[${LABEL_WAIT}]}" \
                    --output "${LABEL_TO_PATH_FILE[${LABEL_WAIT}]}" \
                    "${TLDZONELINK}" &
                LABEL_TO_STATUS[${LABEL_WAIT}]="$!"
                echo "${LABEL_WAIT}: ${LABEL_TO_STATUS[${LABEL_WAIT}]}"
                sleep 1
            else
                sleep 10
            fi
        fi
    fi
done

# Check.
CORRUPT="FALSE"
for LABEL in "${LABELS[@]}"
do
    LABEL_PATH_FILE="${TARGET_PATH}/${LABEL}"
    if [[ -f "${LABEL_TO_PATH_FILE[${LABEL}]}" ]]
    then
        SIZE="${LABEL_TO_SIZE[${LABEL}]}"
        ACTUAL_SIZE=$(stat --format "%s" "${LABEL_TO_PATH_FILE[${LABEL}]}")
        if [[ "${ACTUAL_SIZE}" != "${SIZE}" ]]
        then
            echo "CORRUPT: ${LABEL_TO_PATH_FILE[${LABEL}]} (unexpected size: ${ACTUAL_SIZE})"
            CORRUPT="TRUE"
        fi
    else
        echo "CORRUPT: ${LABEL} (missing)"
        CORRUPT="TRUE"
    fi
done
if [[ "${CORRUPT}" == "TRUE" ]]
then
    exit
fi

# Assemble.
echo "BEGIN: ASSEMBLE..."
cat "${LABEL_TO_PATH_FILE[@]}" > "${TARGET_FILE_NAME}"
echo "DONE: ASSEMBLE"

# Check.
ACTUAL_SIZE=$(stat --format "%s" "${TARGET_PATH_FILE}")
if [[ "${ACTUAL_SIZE}" != "${STATUS_CONTENTLENGTH}" ]]
then
    echo "CORRUPT: ${TARGET_PATH_FILE} (unexpected size: ${ACTUAL_SIZE})"
    exit 1
fi

echo "BEGIN: GUNZIP TEST..."
gunzip --test "${TARGET_PATH_FILE}"
RESULT="${?}"
if [[ "${RESULT}" != "0" ]]
then
    echo "CORRUPT: ${TARGET_PATH_FILE} (gunzip test failed with: ${RESULT})"
    exit 1
fi
echo "DONE: GUNZIP TEST"

# Delete.
#rm --force "${LABEL_TO_PATH_FILE[@]}"
#rm --force "${LABEL_TO_LOG_PATH_FILE[@]}"

################################################################################
# End of file
################################################################################
