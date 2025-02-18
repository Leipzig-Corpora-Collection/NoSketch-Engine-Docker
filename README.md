# NoSketch Engine Docker

Fork of https://github.com/elte-dh/NoSketch-Engine-Docker with customizations for UI and Auth.

This is a [dockerised](https://www.docker.com/) version of [NoSketch Engine](https://nlp.fi.muni.cz/trac/noske), the open source version of [Sketch Engine](https://www.sketchengine.eu/) corpus manager and text analysis software developed by [Lexical Computing Limited](https://www.lexicalcomputing.com/).

This docker image is based on Debian 12 Bookworm and [the NoSketch Engine build and installation process](https://nlp.fi.muni.cz/trac/noske#Buildandinstallation) contains some additional hacks for convenient install and use.
See [Dockerfile](Dockerfile) for details.

## TL;DR

1. `git clone https://git.saw-leipzig.de/wortschatz/nosketch-engine-docker.git`
2. `make build` – to build the docker image
3. `make compile` – to compile sample corpora
4. `make execute` – to execute a Sketch Engine command (`compilecorp`, `corpquery`, etc.) in the docker container (runs a test CLI query on `susanne` corpus by default)
5. `make run` – to launch the docker container
6. Navigate to `http://localhost:10070/` to try the WebUI

## Features

- Easy to add corpora (just add vertical file and registry file to the appropriate location, and compile the corpus with one command)
- CLI commands can be used directly (outside the docker image)
- Works on any domain without changing configuration (without HTTPS and Shibboleth)
- basic auth (updateable easily)
- removed _Shibboleth SP_ and _Let's Encrypt_, see [origin](https://github.com/elte-dh/NoSketch-Engine-Docker)

Corpus configuration recipes to aid compilation of large corpora can be found [here](https://github.com/ELTE-DH/NoSketch-Engine-Docker/tree/main/examples).

## Changes

A few overrides to the source files for the `bonito-open` API and `crystal-open` UI were added to [`noske_files/`](noske_files/) in directories matching the source archives. When building the packages, first the source archives will be extracted and then the override files on top.

For changes, please take a look at the git history, e.g. `git log --stat --oneline --decorate --graph --all --name-status`.
Commits with message _Add base files before changes_ (or _(base files)_) will only add the unchanged source files from the source archives as diff base and in separate new commits our own changes and updates. This allows to look at modifications against the base sources a little bit easier.
Updates of NoSketchEngine sources will also be split into two commits, the first being all the original source files from the new version as diff base, and the second commit that removes all the old version and with our changes applied to the new source files.

See helper scripts [`noske_files/noske-diff.sh`](noske_files/noske-diff.sh) for seeing changes to our override files and [`noske_files/rebase-originals.sh`](noske_files/rebase-originals.sh) for how commits can be split for better diffs.

### crystal-open-2.142 .. crystal-open-2.166.4

Overrides in `noske_files/crystal-open-2.166.4`:

- added Matomo/Piwik monitoring by hooking into the UI routing lib
  - `app/index.html`
  - `app/src/core/Router.js`
  - `app/src/core/Connection.js`
- updated logos
  - `app/favicon.ico`
  - `app/images/`
  - `app/src/core/side-nav/`
- some bugfixes (ske -> noske, missing stuff)
  - `app/src/core/permissions.js` (fix permissions)
  - `app/config.js` (add missing links)
  - `app/src/corpus/` (remove 'basic' and 'shared' corpus tabs, not used)
  - `app/src/dialogs/` (disable any Ske feedback dialogs, remove user Lexonomy settings, fix manage-corpus redirect)
  - `app/src/core/side-nav/side-nav.tag` (remove word sketches, can't provide those anyway)
  - `app/src/concordance/concordance-line-detail-dialog.tag` (`.Refs` access, api: `"error": "AttrNotFound (doc)"`)
- some UI additions
  - `app/src/corpus/` (add sentence count to corpora list)
- disabled youtube integration (and tracking!)
  - `app/config.js`
  - `app/texts/`
- add frequency class value to wordlist
  - `app/src/misc/Misc.js` (column value formatting)
  - `app/src/wordlist/wordlist-result-options-view.tag` (freqcls toggle dis/enable status)
  - `app/src/wordlist/wordlist-result-options.tag` (user attributes updates)
  - `app/src/wordlist/wordlist-result-table.tag` (sorting)
  - `app/src/wordlist/wordlist-tab-advanced.tag` (? initial search options)
  - `app/src/wordlist/Wordlist.meta.js` (freqcls (wlnums) column)
  - `app/src/wordlist/WordlistStore.js` (freqcls in requests)
  - `app/locale` (add "freqcls" labels)
  - `app/texts/en/freqcls.html` (add freqcls description)
- show (new) `struct_attr` and `info` metadata for condordance `Lines[].Links[]`
  - `app/src/concordance/concordance-media-window.scss` (remove divider and spacing if not media on top)
  - `app/src/concordance/concordance-media-window.tag` (show `info` and `struct_attr` metadata)
  - `app/src/concordance/concordance-result.tag` (show `struct_attr` in tooltip)
  - `app/locale` (add "info" labels)

### bonito-open-5.63.9 .. bonito-open-5.71.15

Overrides in `noske_files/bonito-open-5.71.15`:

- fix corpus metadata in `/corpora` request (sizes as numbers)
  - `conccgi.py`
  - `corplib.py`
- fix and cleanup imports
  - `conccgi.py`
  - `usercgi.py`
- remove insecure `clear_cache` method (os access is mitigated with corpname validation but is not really used anyway)
  - `conccgi.py`
- added [FCS](https://git.saw-leipzig.de/text-plus/FCS/fcs-nosketchengine-endpoint) related attributes to API
  - `conccgi.py` (for `/corp_info`: `handle` PID (from `HANDLE`), `fcsrefs` for backlinks (from `FCSREFS`), 'institution' name (from `INSTITUTION`))
  - `corplib.py` (for `/corpora`: `handle` PID, `institution` name)
- for [Wortschatz Leipzig](https://wortschatz-leipzig.de) added some more metadata (e.g., to compute frequency classes etc.)
  - `corplib.py`: `get_ws_info(corpus)` will extract `WSMFW` and `WSMFWF` settings aka _most frequent word_ and its frequency
  - `conccgi.py` --> `wsinfo: { mfw: str|null, mfwf: int|null }` will expose the _most frequent word_ information
- add frequency class value to wordlist
  - `conccgi.py` (freqcls computation in `wordlist` method)
- add `struct_attr` and `info` metadata to condordance `Lines[].Links[]`
  - `conclib.py` (`kwiclines` method)

### manatee-open-2.225.8

Overrides in `noske_files/manatee-open-2.225.8`:

- added missing header file for docker build (`debuild`)
  - `hat-trie/test/str_map.h` (by [ELTE-DH/NoSketch-Engine-Docker](https://github.com/ELTE-DH/NoSketch-Engine-Docker/commit/8186407ab3d3ac39bed59f1bbfb5b7f2db78e5b6#diff-507ccde5eb32a558a2ea7bc57c5ebe5b8d128b9ec28faf2799234ffe5305ed85))

### Basic Auth

- `conf/000-default.conf` (enable basic auth, forward header; block file listing)
- `conf/run.cgi` (parse header, restrict corplist)
- `noske_files/bonito-open-5.63.9/conccgi.py` (add user to corpus)
- `noske_files/crystal-open-2.142/app/locale/`
- `noske_files/crystal-open-2.142/app/src/core/header`
- `noske_files/crystal-open-2.142/app/src/corpus/` (using `username` instead of `userid`)

### NSE Configuration

- `conf/000-default.conf`: increasing _keyword_ (`extract_keywords()`) limit using `SetEnv HTTP_X_KEYWORD_MAX_SIZE 10000`

## Known Issues

- basic auth re-login:\
  Logging in with valid credentials, then logging out and finally trying to login again silently fails due to browser credentials caching. Users then need use the browsers' devtools with cache-clearing active in the network tab to be able to login. No good solution for now.

## Usage

### 1. Get the Docker image

- Build your own image yourself (the process can take 5 minutes or so): `make build IMAGE_NAME=myimage:latest`– be sure to name your image using the `IMAGE_NAME` parameter

### 2. Compile your corpus

1. Put vert file(s) in: `CORPORA_DIR/vert/CORPUS_NAME` directory (SSD)
2. Put config in: `CORPORA_DIR/registry/CORPUS_NAME` file
3. Compile all corpora listed in `CORPORA_DIR/registry` directory using the docker image: `make compile`
    - To compile _one_ corpus at a time (overwriting existing files), use the following command:\
      `make execute CMD="compilecorp --no-ske --recompile-corpus CORPUS_REGISTRY_FILE"`
    - If you want to overwrite all existing indices automatically when running `make compile` set any non-empty value for `FORCE_RECOMPILE` env variable e.g. `make compile FORCE_RECOMPILE=y`

### 3. Run

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
- `make htpasswd`: generate strong password for htaccess authentication, see details in [Basic auth](#basic-auth) section)

## `make` parameters, multiple images and multiple containers

By default,
- the name of the docker image (`IMAGE_NAME`) is `lcc/nosketch-engine:latest`,
- the name of the docker container (`CONTAINTER_NAME`) is `noske`,
- the directory where the corpora metadata and raw input files (vertical) are stored (`CORPORA_DIR`) is `/disk/NoSketchEngine`,
  - the directory with the corpus metadata files (`REGISTRY_DIR`) is `$(CORPORA_DIR)/registry`,
  - the directory with the corpus vertical input files (`VERT_DIR`) is `$(CORPORA_DIR)/vert`,
- the directory where the corpora (compiled, index files; and bonito caches) are stored (`FAST_CORPORA_DIR`) is `/ssd1/NoSketchEngine`,
  - the directory with the compiled corpora files (`COMPILED_DIR`) is `$(FAST_CORPORA_DIR)/data`,
  - the directory with the Bonito corpus cache files (`CACHE_DIR`) is `$(FAST_CORPORA_DIR)/cache`,
  - the directory with the Bonito subcorpus definition files (`SUBCORP_DIR`) is `$(FAST_CORPORA_DIR)/subcorp`,
  - the directory with the Bonito user data files (`USERDATA_DIR`) is `$(FAST_CORPORA_DIR)/options`,
  - the file with the apache2 basic auth user credentials (`SECRETS_FILE`) is `$(pwd)/secrets/htpasswd`,
- the port number which the docker container uses (`PORT`) is `10070`,
- the variable to force recompiling already indexed corpora (`FORCE_RECOMPILE`) is not set (_empty_ or _not set_ means _false_ any other non-zero length value means _true_),
- the citation link (`CITATION_LINK`) is `https://wortschatz-leipzig.de/`,
- the server name (`SERVER_NAME`) is `https://cql.wortschatz-leipzig.de/`,
- the server alias (`SERVER_ALIAS`) is `cql.wortschatz-leipzig.de`,
- the _htpasswd_ file is loaded from ([secrets/htpasswd](secrets) see [secrets/htpasswd.template](secrets) for example) or empty if these files do not exist.

If there is a need to change these, set them as environment variables (e.g. `export IMAGE_NAME=myimage:latest`) or supplement `make` commands with the appropriate values (e.g. `make run PORT=8080`).

E.g. `export IMAGE_NAME=myimage:latest; make build` build an image called `myimage:latest`; and `make run IMAGE_NAME=myimage:latest CONTAINER_NAME=mycontainer PORT=12345` launches the image called `myimage:latest` in a container called `mycontainer` which will use port `12345`.
In the latter case the system will be available at `http://SERVER_NAME:12345/`.

See the table below on which `make` command accepts which parameter:

| command               | `IMAGE_NAME` | `CONTAINER_NAME` | `REGISTRY_DIR` | `VERT_DIR` | `COMPILED_DIR` | `SECRETS_FILE` | Cache and User Data | `PORT` | `FORCE_RECOMPILE` | User Credential Variables | The Other Variables |
|-----------------------|:------------:|:----------------:|:--------------:|:----------:|:--------------:|:--------------:|:-------------------:|:------:|:-----------------:|:-------------------------:|:-------------------:|
| `make build`          |       ✔      |         .        |       .        |     .      |        .       |        .       |          .          |    .   |         .         |            .              |          .          |
| `make compile`        |       ✔      |         .        |      (✔)       |     .      |        ✔       |       (✔)      |          .          |    .   |         ✔         |            .              |          .          |
| `make check`          |       ✔      |         .        |      (✔)       |     .      |       (✔)      |       (✔)      |          .          |    .   |         .         |            .              |          .          |
| `make execute`        |       ✔      |         .        |       ✔        |     ✔      |        ✔       |        ✔       |          .          |    .   |         ✔         |            .              |          ✔          |
| `make execute-no-tty` |       ✔      |         .        |       ✔        |     ✔      |        ✔       |        ✔       |          .          |    .   |         ✔         |            .              |          ✔          |
| `make run`            |       ✔      |         ✔        |       ✔        |     ✔      |        ✔       |        ✔       |          ✔          |    ✔   |         .         |            .              |          ✔          |
| `make connect`        |       .      |         ✔        |       .        |     .      |        .       |        .       |          .          |    .   |         .         |            .              |          .          |
| `make stop`           |       .      |         ✔        |       .        |     .      |        .       |        .       |          .          |    .   |         .         |            .              |          .          |
| `make htpasswd`       |       ✔      |         .        |      (✔)       |    (✔)     |       (✔)      |       (✔)      |          .          |    .   |         .         |            ✔              |          .          |
| `make clean`          |       ✔      |         ✔        |       .        |     .      |        ✔       |        ✔       |          ✔          |    .   |         .         |            .              |          .          |

- Cache and User Data Variables are
  - `CACHE_DIR` (Bonito corpora)
  - `SUBCORP_DIR` (Bonito subcorpora definition)
  - `USERDATA_DIR` (Bonito user data (options))
- User Credential Variables are
  - `USERNAME` and `PASSWORD` (user credentials)
- The Other Variables are
  - `CITATION_LINK` (when logged in, link in dashboard to citations)
  - `SERVER_NAME` and `SERVER_ALIAS` (apache2 configurations)

In the rare case of _multiple different docker images_, be sure to name them differently (by using `IMAGE_NAME`).\
In the more common case of _multiple different docker containers_ running simultaneously, be sure to name them differently (by using `CONTAINER_NAME`) and also be sure to use different port for each of them (by using `PORT`). To handle multiple different sets of corpora be sure to set the directory containing the corpora (`CORPORA_DIR`) accordingly for each container.

If you want to build your own docker image be sure to include the `IMAGE_NAME` parameter into the build command: `make build IMAGE_NAME=myimage:latest` and also provide `IMAGE_NAME=myimage:latest` for every `make` command which accepts this parameter.

## Authentication

Only _basic auth_ authentication is supported, and enabled by default. Configuration are set in [Apache configuration](conf/000-default.conf) and mapped in the [`Makefile`](Makefile).

### Basic auth

Enabled in [`conf/000-default.conf`](conf/000-default.conf) by default. Set username and password in `secrets/htpasswd` (e.g. use `make htpasswd USERNAME="USERNAME" PASSWORD="PASSWD"` shortcut for running `htpasswd` from `apache2-utils` package inside docker)

## Citation link

You can set a link to your publications which you require users to cite.
Set `CITATION_LINK` e.g. `export CITATION_LINK="https://LINK_GOES_HERE"` or in `secrets/env.sh` (see [`secrets/env.sh.template`](secrets/env.sh.template) for example).

The link is displayed in the lower-right corner of the main dashboard if [any type of authentication](#authentication) is set.

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
