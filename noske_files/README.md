# Overrides

Workflow for modifying the Crystal UI sources:

1. Finding relevant source files in original sources using ids/classes ...
2. Create exact path to overrides and copy files, modify it
3. Rebuild Dockerimage

```bash
# extract original sources
mv crystal-open-2.142 crystal-open-2.142-temp
tar xvfz crystal-open-2.142.tar.gz
echo "*" > crystal-open-2.142/.gitignore
mv crystal-open-2.142 crystal-open-2.142-original
mv crystal-open-2.142-temp crystal-open-2.142

# TODO: copy from original and modify
```

---

To update on source archive:

1. download updated source archive
2. run `noske-diff.sh`
3. apply changes
  1. for each file: `patch -p1 < .compare/<archive>-diff/<path-to-patch>.patch`, if sources folder has not been renamed, select the filename of the original (old) version
  2. on error, do manual inspection; to be sure, copy new original source file over our overlay file and then inspect changes (to our intended changes)
4. update versions
