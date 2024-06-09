#!/bin/bash

REGISTRY_DIR=/corpora/registry
DATA_DIR=/corpora/data

if [[ -n "$(ls ${DATA_DIR}/* 2> /dev/null)" ]]; then
    echo 'WARNING: This will delete all indices and recompile all corpora!' >&2
    if [[ -n "$FORCE_RECOMPILE" ]]; then
        echo 'INFO: Continuing in force recompile mode' >&2
    else
        echo 'Do you want to continue? [y/N]' >&2
        read -rN1 ans
        echo
        if [[ ! "${ans:-N}" =~ ^[yY] ]]; then
            echo "To recompile a specific corpus, run" \
             "'make execute CMD=\"compilecorp --no-ske --recompile-corpus CORPUS_REGISTRY_FILE\"' instead." >&2
            exit 1
        fi
    fi
fi

compile_single_corpus () {
    CORP_FILE="$1"
    echo "Running: compilecorp --no-ske --recompile-corpus \"${CORP_FILE}\"" >&2
    compilecorp --no-ske --recompile-corpus "${CORP_FILE}" || (echo "Error: return code '$?'" ; exit 255)
}
export -f compile_single_corpus

# Compile corpora
find ${REGISTRY_DIR} -type f -print0 | sort -z | xargs -r -0 -I {} -n 1 bash -c 'compile_single_corpus "$1"' _ {} \;
