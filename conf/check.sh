#!/bin/bash

REGISTRY_DIR=/corpora/registry

_run_check() {
    CORP_FILE="${1##$REGISTRY_DIR/}"
    CMD="corpcheck ${CORP_FILE}"

    stdbuf -oL bash -c "${CMD}" 2>&1 |
    while IFS= read -r line
    do
        echo -e "\033[2m$(printf %-20s ${CORP_FILE} | tr " " " ")\033[0m ${line}"
    done
    CMD_STATUS="${PIPESTATUS[0]}"

    [ $CMD_STATUS -eq 0 ] || exit 255
}
export REGISTRY_DIR
export -f _run_check

find ${REGISTRY_DIR} -type f ! -iname "*.disabled" -print0 | sort -z | xargs -r -0 -I {} -n 1 bash -c '_run_check "$1"' _ {} \;
