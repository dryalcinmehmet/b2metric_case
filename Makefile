SHELL=/bin/bash

ifneq (,$(findstring xterm,${TERM}))
	BLACK        := $(shell tput -Txterm setaf 0)
	RED          := $(shell tput -Txterm setaf 1)
	GREEN        := $(shell tput -Txterm setaf 2)
	YELLOW       := $(shell tput -Txterm setaf 3)
	LIGHTPURPLE  := $(shell tput -Txterm setaf 4)
	PURPLE       := $(shell tput -Txterm setaf 5)
	BLUE         := $(shell tput -Txterm setaf 6)
	WHITE        := $(shell tput -Txterm setaf 7)
	RESET := $(shell tput -Txterm sgr0)
else
	BLACK        := ""
	RED          := ""
	GREEN        := ""
	YELLOW       := ""
	LIGHTPURPLE  := ""
	PURPLE       := ""
	BLUE         := ""
	WHITE        := ""
	RESET        := ""
endif

# set target color
TARGET_COLOR := $(BLUE)

POUND = \#

.PHONY: no_targets__ info help build deploy doc
	no_targets__:

.DEFAULT_GOAL := help

help:
	@echo ""
	@echo "    ${GREEN}::::::::::::::::::::::::::::::::${RED}Makefile Commands${RESET} ${GREEN}::::::::::::::::::::::::::::::::${RESET}"
	@echo ""
	@echo "   ${LIGHTPURPLE}Type the commands below into the terminal. You can find examples for each other.${LIGHTPURPLE}"
	@echo ""
	@echo "Examples:"
	@echo ""
	@echo "  ${PURPLE}|${PURPLE} devdown:  $(POUND)$(POUND) help for devdown"
	@echo "  ${YELLOW}| 	--> For stopping and removing development containers, networks and volumes.${YELLOW}"
	@echo "  |  >> ${GREEN}make devdown${GREEN}"
	@echo ""
	@echo "  ${PURPLE}|${PURPLE} devup:  $(POUND)$(POUND) help for devup"
	@echo "  ${YELLOW}| 	--> For starting and removing development containers, networks and volumes${YELLOW} ${RED}with tests in debugger mode.${RED}"

	@echo ""
	@echo "  ${PURPLE}|${PURPLE} install:  $(POUND)$(POUND) help for install"
	@echo "  ${YELLOW}| 	--> For Installing ubuntu requirements.${YELLOW}"
	@echo "  |  >> ${GREEN}make install${GREEN}"
	@echo ""

.PHONY : install
install:  ## Install dependencies for Ubuntu 20.04
	@echo "${GREEN}-----------------------------------------------------------------------------------------------------------------${RESET}"
	@echo "${PURPLE}--> Installing Ubuntu packages...${RESET}"
	@echo "${GREEN}-----------------------------------------------------------------------------------------------------------------${RESET}"
	$(shell  sudo rm -rf /var/cache/apt/archives/lock)
	$(shell  sudo rm -rf /var/lib/dpkg/lock)
	$(shell  sudo rm -rf /var/lib/dpkg/lock-frontend)
	$(shell  sudo rm -f /etc/gitlab-runner/config.toml)
	$(shell  sudo rm -rf /var/lib/apt/lists/lock)
	$(shell  sudo dpkg --configure -a)
	sudo apt update && sudo apt install -y apt-utils graphviz git libmariadb3 \
		postgresql gcc python3-pip python3-dev musl-dev netcat libpq-dev \
		autoconf automake libffi-dev libtool openssl cargo \
		gdal-bin libmysqlclient-dev libgdal-dev python3-gdal binutils libproj-dev pkg-config -y
	@echo "${PURPLE}--> Disabling PostgreSQL systemd service to prevent port clash with database container...${RESET}"
	sudo systemctl stop postgresql.service
	sudo systemctl disable postgresql.service
	@echo "${GREEN}-----------------------------------------------------------------------------------------------------------------${RESET}"
	@echo "${PURPLE}--> Installing Development tools...${RESET}"
	@echo "${GREEN}-----------------------------------------------------------------------------------------------------------------${RESET}"
	python3 -m pip install black==22.3.0
	python3 -m pip install isort==5.10.1
	python3 -m pip install setuptools==57.5.0
	sudo rm -rf .poetry_cache/virtualenvs/*
	python3 -m pip install poetry==1.1.12
	make install-gitlab-runner || true
	curl -fsSL https://get.docker.com -o get-docker.sh
	sh get-docker.sh
	sudo apt-get update
	make docker-compose
	sudo groupadd docker || true
	sudo usermod -aG docker $(USER)
	sudo usermod -aG docker gitlab-runner
	newgrp docker
	docker run hello-world

.PHONY : docker-compose
docker-compose:  ## Installing docker compose.
	@echo "${GREEN}-----------------------------------------------------------------------------------------------------------------${RESET}"
	@echo "${PURPLE}--> Installing Docker Compose...${RESET}"
	@echo "${GREEN}-----------------------------------------------------------------------------------------------------------------${RESET}"
	sudo rm -rf /usr/local/bin/docker-compose | true
	sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(shell uname -s)-$(shell uname -m)" -o /usr/local/bin/docker-compose
	sudo chmod +x /usr/local/bin/docker-compose
	docker-compose --version


.PHONY : get-version
get-version:  ## Get latest version
	@echo "${PURPLE}$(shell cat '.env.dev' | grep API_VERSION)${RESET}"

.PHONY : down
down:  ## Docker down
	@echo "${PURPLE}Docker compose down!..."
	docker-compose -f docker-compose.yml down -v
	docker-compose -f docker-compose.yml down -v	
	docker-compose down --volumes --remove-orphans

.PHONY : dev
dev:  ## Docker dev
	@echo "${PURPLE}Creating custom_net external...${RESET}"
	docker network create custom_net || echo "${PURPLE}custom_net already exist!${RESET}"

	@echo "${RED}Docker compose down!${RESET}"
	docker-compose -f docker-compose.yml down -v
	docker-compose -f docker-compose.yml down -v

	@echo "${YELLOW}Docker compose up!...${RESET}"
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose -f docker-compose.yml up --build -d
	COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose -f docker-compose.yml up --build -d
