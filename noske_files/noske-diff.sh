#!/bin/bash

DN_COMPARE=.compare
DN_CWD=$(pwd)
DN_DIFF_PART="diff"

mkdir -p $DN_COMPARE

# let git ignore all those new files
echo "*" > ${DN_COMPARE}/.gitignore

function findRelevantChangedFiles () {
    NAME=$1
    DN_OLD=$2
    DN_NEW=$3
    DN_OVERWRITES=$4

    # filter for different files only
    CHANGED_FILES=($(
        for fn in $(find ${DN_NEW}/ -type f | cut -d'/' -f2- | sort -n); do
            diff --new-file --brief "${DN_OLD}/$fn" "${DN_NEW}/$fn" >/dev/null 2>&1
            isdiff=$?
            if [[ $isdiff -eq 1 ]]; then
                echo "$fn"
            fi
        done
    ))
    >&2 echo "Found ${#CHANGED_FILES[@]} changed files."
    if [[ "${#CHANGED_FILES[@]}" -eq 0 ]]; then
        return
    fi

    # check which of those changed files would affect us
    FILES_TO_CHECK=($(
        for fn in ${CHANGED_FILES[@]}; do
            test -f "${DN_CWD}/${DN_OVERWRITES}/$fn" >/dev/null 2>&1
            fnexists=$?
            if [[ $fnexists -eq 0 ]]; then
                echo "$fn"
            fi
        done

        # only for crystal
        if [[ "$NAME" = "crystal-open" ]]; then
            >&2 echo "Only for \"$NAME\": check for new <iframe> elements..."
            for fn in ${CHANGED_FILES[@]}; do
                if [[ "$fn" == app/texts/* ]]; then
                    grep --no-messages --silent --fixed-strings "</iframe>" "${DN_NEW}/$fn"
                    found=$?
                    if [[ $found -eq 0 ]]; then
                        echo "$fn"
                    fi
                fi
            done
        fi
    ))
    FILES_TO_CHECK=($(printf "%s\n" "${FILES_TO_CHECK[@]}" | sort -u))
    >&2 echo "Need to check ${#FILES_TO_CHECK[@]} files!"

    # return list of files to inspect
    for fn in ${FILES_TO_CHECK[@]}; do
        echo "$fn"
    done
}

function checkForPossibleConflicts () {
    NAME="$1"
    >&2 echo "Checking \"$NAME\" ..."

    # our overwrites folder
    DN_OVERWRITES=$(find . -maxdepth 1 -type d -iname "${NAME}*" | xargs -I {} basename {} \; | sort -n -r | head -n 1)

    # artifact files/source archives
    FILES=($(find . -maxdepth 1 -type f -iname "${NAME}*.tar.gz" | xargs -I {} basename {} \; | sort -n ))
    if [[ "${#FILES[@]}" -ne 2 ]]; then
        >&2 echo "Expected exactly two source archives for \"${NAME}\"? Abort ..."
        >&2 echo "Files: ${FILES[@]}"
        return
    fi

    FN_OLD=${FILES[0]}
    FN_NEW=${FILES[1]}
    DN_OLD=${FN_OLD%.tar.gz}
    DN_NEW=${FN_NEW%.tar.gz}

    # artifact versions
    VERSIONS=($(for fn in ${FILES[@]}; do echo $fn ; done | xargs -I {} sh -c 'fn=$1 ; version=${fn#'"$NAME"'-} ; version=${version%.tar.gz} ; echo $version' -- {} \;))
    >&2 echo "Compare versions: ${VERSIONS[@]}"

    cd $DN_COMPARE

    # extract both source archives
    for fn in ${FILES[@]}; do
        tar xfz $DN_CWD/$fn
    done

    # find relevant changed files
    FILES_TO_CHECK=($(findRelevantChangedFiles "$NAME" "$DN_OLD" "$DN_NEW" "$DN_OVERWRITES"))

    # create diff files for files that we have changes for
    DN_DIFFS="${DN_NEW}-${DN_DIFF_PART}"
    rm -rf "${DN_DIFFS}" >/dev/null 2>&1
    if [[ "${#FILES_TO_CHECK[@]}" -gt 0 ]]; then
        >&2 echo "Creating patches in \"${DN_COMPARE}/${DN_DIFFS}/\" ..."
        mkdir "${DN_DIFFS}"
        for fn in ${FILES_TO_CHECK[@]}; do
            dn=$(dirname $fn)
            mkdir -p "${DN_DIFFS}/$dn"
            diff -Naur "${DN_OLD}/$fn" "${DN_NEW}/$fn" > "${DN_DIFFS}/${fn}.patch"
        done

        # applying patches?
        # for fn in ${FILES_TO_CHECK[@]}; do
        #     patch "${DN_CWD}/${DN_OVERWRITES}/$fn" "${DN_DIFFS}/${fn}.patch"
        # done
    fi

    # clean up source archives
    for fn in ${FILES[@]}; do
        rm -r "${fn%.tar.gz}"
    done

    cd ..

    # return list of files to inspect
    for fn in ${FILES_TO_CHECK[@]}; do
        echo "$fn"
    done
}

checkForPossibleConflicts "manatee-open"
echo ""

checkForPossibleConflicts "bonito-open"
echo ""

checkForPossibleConflicts "gdex"
echo ""

checkForPossibleConflicts "crystal-open"
