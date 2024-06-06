# tutorial on how to add original files for better diffs (afterwards)
# -------------------------------------------------------------------

# find commit before our changes (to add base files)
git rebase -i <commit>
# set top-most commit to "e"/"edit" and confirm rebase

# unstage everything from commit
git reset HEAD~

# which sources to update, e.g.
SRC=bonito-open-5.71.15

# save changes
mv ${SRC} ${SRC}-bak
# extract originals
tar xfz ${SRC}.tar.gz
# stage originals for all change files
find ${SRC}-bak/ -type f | cut -d'/' -f2- | xargs -I {} sh -c 'fn=$1 ; git add '"${SRC}"'/$fn' -- {} \;
# commit base files
git commit -m "... base files ..."

# remove base files
rm -r ${SRC}
# update to our changes
mv ${SRC}-bak ${SRC}
# stage
git add ${SRC}
# commit
git commit -m "... changes ..."

# and stage/commit everything that is still open (see `git status` ...)

# continue rebase
git rebase --continue

# probably (but please confirm beforehand that there are not changes lost between original HEAD and new HEAD!)
git push --force origin main
