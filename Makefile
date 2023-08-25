IMAGE_NAME?=lcc/nosketch-engine
CONTAINER_NAME?=noske

CORPORA_DIR?=/disk/NoSketchEngine
FAST_CORPORA_DIR?=/ssd1/NoSketchEngine

REGISTRY_DIR?=$(CORPORA_DIR)/registry
VERT_DIR?=$(CORPORA_DIR)/vert
COMPILED_DIR?=$(FAST_CORPORA_DIR)/data
CACHE_DIR?=$(FAST_CORPORA_DIR)/cache
SUBCORP_DIR?=$(FAST_CORPORA_DIR)/subcorp
USERDATA_DIR?=$(FAST_CORPORA_DIR)/options
SECRETS_FILE=$$(pwd)/secrets/htpasswd


#HOSTNAME?=$(shell hostname -I | cut -f1 -d' ')
HOSTNAME?=127.0.0.1
PORT?=10070
SERVER_NAME?=https://cql.wortschatz-leipzig.de/
SERVER_ALIAS?=cql.wortschatz-leipzig.de
CITATION_LINK?=https://wortschatz-leipzig.de/
CMD?=corpquery susanne "[word=\"Mardi\"][word=\"Gras\"]"


all: build run
.PHONY: all


# Build $(IMAGE_NAME) docker image
build:
	docker build -t $(IMAGE_NAME) .
.PHONY: build


# Run $(CONTAINER_NAME) container from $(IMAGE_NAME) image, mount $(CORPORA_DIR), use host port $(PORT)
#  and set various environment variables
run:
	@make -s stop
	@make -s run-pre
	docker run -d --restart=unless-stopped --name $(CONTAINER_NAME) -p 127.0.0.1:$(PORT):80 \
	 --mount type=bind,src=$(REGISTRY_DIR),dst=/corpora/registry,readonly \
	 --mount type=bind,src=$(VERT_DIR),dst=/corpora/vert,readonly \
	 --mount type=bind,src=$(COMPILED_DIR),dst=/corpora/data,readonly \
	 --mount type=bind,src=$(CACHE_DIR),dst=/var/lib/bonito/cache \
	 --mount type=bind,src=$(SUBCORP_DIR),dst=/var/lib/bonito/subcorp \
	 --mount type=bind,src=$(USERDATA_DIR),dst=/var/lib/bonito/options \
	 --mount type=bind,src=$(SECRETS_FILE),dst=/var/lib/bonito/htpasswd \
	 --mount type=volume,src=$(CONTAINER_NAME)-registration,dst=/var/lib/bonito/registration \
	 --mount type=volume,src=$(CONTAINER_NAME)-jobs,dst=/var/lib/bonito/jobs \
     -e SERVER_NAME="$(SERVER_NAME)" -e SERVER_ALIAS="$(SERVER_ALIAS)" -e CITATION_LINK="$(CITATION_LINK)" \
     $(IMAGE_NAME):latest
	@echo 'URL: http://$(HOSTNAME):$(PORT)/'
.PHONY: run

run-pre:
	[ -f "$(SECRETS_FILE)" ] || touch $(SECRETS_FILE)
	mkdir -p $(USERDATA_DIR) $(SUBCORP_DIR) $(CACHE_DIR)
	docker volume create $(CONTAINER_NAME)-registration
	docker volume create $(CONTAINER_NAME)-jobs
.PHONY: run-pre


# Stop running $(CONTAINER_NAME) container
stop:
	@if [ "$$(docker container ls -f name=$(CONTAINER_NAME) -q)" ] ; then \
        docker container stop $(CONTAINER_NAME) ; \
        docker container rm $(CONTAINER_NAME) ; \
    else \
        echo 'No running $(CONTAINER_NAME) container!' >&2 ; \
    fi
.PHONY: stop


# Connect to running $(CONTAINER_NAME) container, start a bash shell
connect:
	docker exec -it $(CONTAINER_NAME) /bin/bash
.PHONY: connect


# Execute commmand in CMD variable and set various environment variables
execute:
	docker run --rm -it \
	 --mount type=bind,src=$(REGISTRY_DIR),dst=/corpora/registry,readonly \
	 --mount type=bind,src=$(VERT_DIR),dst=/corpora/vert,readonly \
	 --mount type=bind,src=$(COMPILED_DIR),dst=/corpora/data \
	 --mount type=bind,src=$(SECRETS_FILE),dst=/var/lib/bonito/htpasswd \
	 -e FORCE_RECOMPILE="$(FORCE_RECOMPILE)" \
     -e SERVER_NAME="$(SERVER_NAME)" -e SERVER_ALIAS="$(SERVER_ALIAS)" -e CITATION_LINK="$(CITATION_LINK)" \
     $(IMAGE_NAME):latest "$(CMD)"
.PHONY: execute

execute-no-tty:
	docker run --rm \
	 --mount type=bind,src=$(REGISTRY_DIR),dst=/corpora/registry,readonly \
	 --mount type=bind,src=$(VERT_DIR),dst=/corpora/vert,readonly \
	 --mount type=bind,src=$(COMPILED_DIR),dst=/corpora/data \
	 -e FORCE_RECOMPILE="$(FORCE_RECOMPILE)" \
     -e SERVER_NAME="$(SERVER_NAME)" -e SERVER_ALIAS="$(SERVER_ALIAS)" -e CITATION_LINK="$(CITATION_LINK)" \
     $(IMAGE_NAME):latest "$(CMD)"
.PHONY: execute-no-tty


# Compile all corpora
compile:
	@make -s execute IMAGE_NAME=$(IMAGE_NAME) FORCE_RECOMPILE=$(FORCE_RECOMPILE) CMD=compile.sh
	docker run --rm -it \
	 --mount type=bind,src=$(COMPILED_DIR),dst=/data \
	 debian:bullseye-slim \
	 chown -R 1002:1002 /data
.PHONY: compile


# Check all corpora (skip "NAME.disabled")
check:
	@make -s execute IMAGE_NAME=$(IMAGE_NAME) CMD=check.sh
.PHONY: check


# Create a strong password with htpasswd command inside the docker container
htpasswd:
	@make -s execute IMAGE_NAME=$(IMAGE_NAME) CMD="htpasswd -bB /var/lib/bonito/htpasswd \"$(USERNAME)\" \"$(PASSWORD)\""


# Stop container, remove image, remove compiled corpora
clean:
	@make -s stop CONTAINER_NAME=$(CONTAINER_NAME)
	docker volume rm $(CONTAINER_NAME)-registration
	docker volume rm $(CONTAINER_NAME)-jobs
	docker image rm -f $(IMAGE_NAME)
	sudo rm -vrf $(CACHE_DIR)/*/
	sudo rm -vrf $(USERDATA_DIR)/*
	sudo rm -vrf $(SUBCORP_DIR)/*
	sudo rm -vrf $(COMPILED_DIR)/*
.PHONY: clean
