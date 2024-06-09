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
