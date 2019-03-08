#!/bin/bash

NUMBER_COMMITS=$1
if [[ -z $NUMBER_COMMITS ]]; then
    echo Specify number of commit to add notes
    exit 1
fi

set -x

COMMITS=$(git log -$NUMBER_COMMITS --oneline --pretty=format:"%h" | tr " " "\n")

GIT_NOTES="git notes"
cnt=0
for commit in $COMMITS; do
    cnt=$((cnt+1))
    ${GIT_NOTES} add -f -m "Testing notes ${cnt}\npackit_test=yes" ${commit}
done

cnt=0
for commit in $COMMITS; do
    cnt=$((cnt+1))
    NOTE=$(git notes show ${commit})
    echo Note is: ${NOTE}
done

COMMIT_2=$(echo ${COMMITS} | cut -d ' ' -f 3)
NOTE2=$(git notes show ${COMMIT_2})

echo "2nd note is ${NOTE2}"
