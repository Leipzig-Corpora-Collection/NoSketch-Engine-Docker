# NoSketch Engine Docker

Fork of https://github.com/elte-dh/NoSketch-Engine-Docker

This is a [dockerised](https://www.docker.com/) version of [NoSketch Engine](https://nlp.fi.muni.cz/trac/noske),
 the open source version of [Sketch Engine](https://www.sketchengine.eu/) corpus manager and text analysis software
 developed by [Lexical Computing Limited](https://www.lexicalcomputing.com/).

This docker image is based on Debian 11 Bullseye and
 [the NoSketch Engine build and installation process](https://nlp.fi.muni.cz/trac/noske#Buildandinstallation) contains
 some additional hacks for convenient install and use.
See [Dockerfile](Dockerfile) for details.

## TL;DR

1. `git clone https://git.saw-leipzig.de/wortschatz/nosketch-engine-docker.git`
2. `make build` – to build the docker image
3. `make compile` – to compile sample corpora
4. `make execute` – to execute a Sketch Engine command (`compilecorp`, `corpquery`, etc.) in the docker container
    (runs a test CLI query on `susanne` corpus by default)
5. `make run` – to launch the docker container
6. Navigate to `http://localhost:10070/` to try the WebUI

## Features

- Easy to add corpora (just add vertical file and registry file to the appropriate location,
   and compile the corpus with one command)
- CLI commands can be used directly (outside the docker image)
- Works on any domain without changing configuration (without HTTPS and Shibboleth)
- ~~(optional) Shibboleth SP (with eduid.hu)~~ (removed, see [origin](https://github.com/elte-dh/NoSketch-Engine-Docker))
- (optional) basic auth (updateable easily)
- ~~(optional) HTTPS with Let's Encrypt (automatic renewal with [traefik proxy](https://traefik.io/traefik/))~~ (removed)

Corpus configuration recipes to aid compilation of large corpora can be found [here](https://github.com/ELTE-DH/NoSketch-Engine-Docker/tree/main/examples).

## Usage

### 1. Get the Docker image

- Build your own image yourself (the process can take 5 minutes or so): `make build IMAGE_NAME=myimage`– be sure
   to name your image using the `IMAGE_NAME` parameter

### 2. Compile your corpus

1. Put vert file(s) in: `corpora/vert/CORPUS_NAME` directory
2. Put config in: `corpora/registry/CORPUS_NAME` file
3. Compile all corpora listed in [`corpora/registry`](corpora/registry) directory using the docker image: `make compile`
    - To compile _one_ corpus at a time (overwriting existing files), use the following command:
      `make execute CMD="compilecorp --no-ske --recompile-corpus CORPUS_REGISTRY_FILE"`
    - If you want to overwrite all existing indices automatically when running `make compile` set any non-empty value
       for `FORCE_RECOMPILE` env variable e.g. `make compile FORCE_RECOMPILE=y`

### 3. Run

(Optional, only recommended if variables are altered)

Customise the environment variables in `secrets/env.sh` (see [`secrets/env.sh.template`](secrets/env.sh.template)
 for example) and _export_ them into the current shell with `source secrets/env.sh`

#### 3a. Run the container

1. Run docker container: `make run`
2. Navigate to `http://SERVER_NAME:10070/` to use

#### 3b. CLI Usage

- `make execute`: runs NoSketch Engine CLI commands using the docker image. Specify the command to run in the `CMD` parameter.
  For example:
  - `make execute CMD='corpinfo -s susanne'`\
    gives info about the _susanne_ corpus
  - `make execute CMD='corpquery emagyardemo "[lemma=\"és\"]"'`\
    runs the specified query on the _emagyardemo_ corpus and gives 2 hits.\
    Mind the use of quotation marks: `\"` inside `"` inside `'`.
- `make connect`: gives a shell to a running container

### 4. Additional commands

- `make stop`: stops the container
- `make clean`: stops the container, _removes indices for all corpora_ and deletes docker image – __use with caution!__
- `make htpasswd`: generate strong password for htaccess authentication (must restart a container to apply; see details
   in [Basic auth](#basic-auth) section)

## `make` parameters, multiple images and multiple containers

By default,
- the name of the docker image (`IMAGE_NAME`) is `eltedh/nosketch-engine`,
- the name of the docker container (`CONTAINTER_NAME`) is `noske`,
- the directory where the corpora are stored (`CORPORA_DIR`) is `$(pwd)/corpora`,
- the port number which the docker container uses (`PORT`) is `10070`,
- the variable to force recompiling already indexed corpora (`FORCE_RECOMPILE`) is not set
   (_empty_ or _not set_ means _false_ any other non-zero length value means _true_),
- the citation link (`CITATION_LINK`) is `https://github.com/elte-dh/NoSketch-Engine-Docker`,
- the server name required for Let's Encrypt and/or Shibboleth (`SERVER_NAME`) is `https://sketchengine.company.com/`
   (mandatory for [`docker-compose.yml`](docker-compose.yml)),
- the server alias required for Let's Encrypt and/or Shibboleth (`SERVER_ALIAS`) is `sketchengine.company.com`
   (mandatory for [`docker-compose.yml`](docker-compose.yml)),
- the e-mail address required by Let's Encrypt (`LETS_ENCRYPT_EMAIL`) is not set (mandatory for Let's Encrypt and
   [`docker-compose.yml`](docker-compose.yml)),
- the _htaccess_ and _htpasswd_ files (`HTACCESS`, `HTPASSWD`) are loaded from ([secrets/{htaccess,htpasswd}](secrets)
   see [secrets/{htaccess.template,htpasswd.template}](secrets) for example) or empty if these files do not exist
   (mandatory for [`docker-compose.yml`](docker-compose.yml)).

If there is a need to change these, set them as environment variables (e.g. `export IMAGE_NAME=myimage`)
 or supplement `make` commands with the appropriate values (e.g. `make run PORT=8080`).

E.g. `export IMAGE_NAME=myimage; make build` build an image called `myimage`; and
`make run IMAGE_NAME=myimage CONTAINER_NAME=mycontainer PORT=12345` launches the image called `myimage` in a container
 called `mycontainer` which will use port `12345`.
In the latter case the system will be available at `http://SERVER_NAME:12345/`.

See the table below on which `make` command accepts which parameter:

| command            | `IMAGE_NAME` | `CONTAINER_NAME` | `CORPORA_DIR` | `PORT` | `FORCE_RECOMPILE` | `USERNAME` | `PASSWORD` | The Other Variables |
|--------------------|:------------:|:----------------:|:-------------:|:------:|:-----------------:|:----------:|:----------:|:-------------------:|
| `make pull`        |       ✔      |         .        |       .       |    .   |         .         |      .     |      .     |          .          |
| `make build`       |       ✔      |         .        |       .       |    .   |         .         |      .     |      .     |          .          |
| `make compile`     |       ✔      |         .        |       .       |    .   |         ✔         |      .     |      .     |          .          |
| `make execute`     |       ✔      |         .        |       ✔       |    .   |         ✔         |      .     |      .     |          ✔          |
| `make run`         |       ✔      |         ✔        |       ✔       |    ✔   |         .         |      .     |      .     |          ✔          |
| `make connect`     |       .      |         ✔        |       .       |    .   |         .         |      .     |      .     |          .          |
| `make stop`        |       .      |         ✔        |       .       |    .   |         .         |      .     |      .     |          .          |
| `make clean`       |       ✔      |         ✔        |       ✔       |    .   |         .         |      .     |      .     |          .          |
| `make htpasswd`    |       ✔      |         .        |       .       |    .   |         .         |      ✔     |      ✔     |          .          |

- The Other Variables are
    - `CITATION_LINK`
    - `SERVER_NAME` and `SERVER_ALIAS`
    - `HTACCESS` and `HTPASSWD`

In the rare case of _multiple different docker images_, be sure to name them differently (by using `IMAGE_NAME`).\
In the more common case of _multiple different docker containers_ running simultaneously,
be sure to name them differently (by using `CONTAINER_NAME`) and also be sure to use different port for each of them
 (by using `PORT`). To handle multiple different sets of corpora be sure to set the directory containing the corpora
 (`CORPORA_DIR`) accordingly for each container.

If you want to build your own docker image be sure to include the `IMAGE_NAME` parameter into the build command:
 `make build IMAGE_NAME=myimage` and also provide `IMAGE_NAME=myimage` for every `make` command
 which accepts this parameter.

A convenient solution for managing many environment variables in an easy and reproducible way
 (e.g. for [`docker-compose.yml`](docker-compose.yml)) is to customise and source `secrets/env.sh` (based on
 [`secrets/env.sh.template`](`secrets/env.sh.template`)) before running the actual command:
 `source secrets/env.sh; docker-compose up -d` or `source secrets/env.sh; make run`.
 See [`secrets/env.sh.template`](secrets/env.sh.template) for example configuration.

## Authentication

Two types of authentication is supported: _basic auth_ and _Shibboleth_

### Basic auth

1. Copy and uncomment relevant config lines from [`secrets/htaccess.template`](secrets/htaccess.template) into
    `secrets/htaccess` and set username and password in `secrets/htpasswd`
    (e.g. use `make htpasswd USERNAME="USERNAME" PASSWORD="PASSWD" >> secrets/htpasswd` shortcut
    for running `htpasswd` from `apache2-utils` package inside docker)
2. [Run or restart the container to apply](#3a-run-the-container) or
    [(re)build your custom image](#1-get-the-docker-image)

## Citation link

You can set a link to your publications which you require users to cite.
Set `CITATION_LINK` e.g. `export CITATION_LINK="https://LINK_GOES_HERE"` or in `secrets/env.sh`
 (see [`secrets/env.sh.template`](secrets/env.sh.template) for example).

The link is displayed in the lower-right corner of the main dashboard if [any type of authentication](#authentication)
 is set.

## Similar projects

- https://github.com/elte-dh/NoSketch-Engine-Docker (original)
- https://hub.docker.com/r/acdhch/noske

## License

The following files in this repository are from https://nlp.fi.muni.cz/trac/noske and have their own license:
- `noske_files/manatee-open-*.tar.gz` (GPLv2+)
- `noske_files/bonito-open-*.tar.gz` (GPLv2+)
- `noske_files/crystal-open-*.tar.gz` (GPLv3)
- `noske_files/gdex-*.tar.gz` (GPLv3)
- Susanne sample corpus: `data/corpora/susanne/vertical` and `data/registry/susanne`

The rest of the files are licensed under the Lesser GNU GPL version 3 or any later.
