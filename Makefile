# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

export JUJU_TEST_CHARM=redis
export JUJU_REPOSITORY=

# Override those values to run functional tests with a different environment
# or Juju series.
SERIES=trusty

# Define system Debian dependencies: run "make sysdeps" to install them.
# Please keep them in alphabetical order.
SYSDEPS = charm-tools juju-core juju-local python-dev python-pip \
	python-virtualenv rsync

PYTHON = python
VENV = .venv
VENV_ACTIVATE = $(VENV)/bin/activate
NOSE = $(VENV)/bin/nosetests
PIP = $(VENV)/bin/pip
FTESTS=$(shell find -L tests -type f -executable | sort)

.DEFAULT_GOAL := $(VENV_ACTIVATE)

.PHONY: help
help:
	@echo -e 'Redis charm - list of make targets:\n'
	@echo 'make - Set up the development and testing environment.'
	@echo 'make test - Run tests (including unit and functional tests).'
	@echo 'make lint - Run linter and pep8.'
	@echo 'make check - Run all the tests and lint.'
	@echo 'make unittest - Run unit tests.'
	@echo 'make ftest - Run functional tests.'
	@echo 'make clean - Get rid of bytecode files and virtual envs.'
	@echo 'make deploy - Deploy the local copy of the charm.'
	@echo -e '\nWhen using "make deploy" it is possible to override the series'
	@echo 'with the SERIES environment variable and the service name with '
	@echo 'the JUJU_SERVICE_NAME environment variable, for instance:'
	@echo '  make deploy SERIES=precise JUJU_SERVICE_NAME=myredis'
	@echo -e '\nWhen using "make deploy" or "make test" or "make ftest" it '
	@echo 'is possible to override the Juju environment that will be used '
	@echo 'with the JUJU_ENV environment variable, for instance:'
	@echo '  make test JUJU_ENV=ec2'

.PHONY: sysdeps
sysdeps:
	sudo apt-get install --yes $(SYSDEPS)

$(VENV_ACTIVATE): test-requirements.pip
	virtualenv --distribute -p $(PYTHON) $(VENV)
	$(PIP) install -r test-requirements.pip || \
		(touch test-requirements.pip; exit 1)
	@touch $(VENV_ACTIVATE)

.PHONY: bundletester
bundletester: $(VENV_ACTIVATE)
	$(PIP) install bundletester
	$(VENV)/bin/bundletester -l DEBUG

.PHONY: clean
clean:
	-$(RM) -rfv $(VENV) .coverage
	find . -name '*.pyc' -delete

.PHONY: check
check: lint test
	juju charm proof

.PHONY: lint
lint: $(VENV_ACTIVATE)
	@$(VENV)/bin/flake8 --show-source --exclude=$(VENV) \
		--filename *.py,install,generic-hook \
		hooks/ tests/ unit_tests/

.PHONY: jenv
jenv:
	$(eval JENV := $(shell JUJU_ENV=$(JUJU_ENV) juju switch))

.PHONY: deploy
deploy: jenv
	@# The use of readlink below is required for OS X.
	@$(eval export JUJU_REPOSITORY:=$(shell mktemp -d `readlink -f /tmp`/temp.XXXX))
	@echo "JUJU_REPOSITORY is $(JUJU_REPOSITORY)"
	@# Setting up the Juju repository.
	@mkdir $(JUJU_REPOSITORY)/${SERIES}
	@rsync -a . $(JUJU_REPOSITORY)/${SERIES}/$(JUJU_TEST_CHARM) \
		--exclude .git --exclude .bzr --exclude tests --exclude unit_tests
	@# Deploying the charm.
	juju deploy -e $(JENV) local:${SERIES}/$(JUJU_TEST_CHARM) $(JUJU_SERVICE_NAME)

.PHONY: test
test: unittest ftest

.PHONY: ftest
ftest: $(VENV_ACTIVATE) jenv
	@juju bootstrap -e $(JENV) --keep-broken --upload-tools || \
		echo "reusing already bootstrapped $(JENV) environment"
	@ # Wait for the environment to be ready.
	@juju status -e $(JENV)
	@# Setting the path is required because internally amulet calls
	@# juju-deployer using subprocess.
	PATH="$(VENV)/bin:$(PATH)" $(NOSE) --verbosity 2 -s -x $(FTESTS)
	@# Clean up deployer garbage.
	@-$(RM) -rf trusty
	@echo "Done! Remember to destroy the environment with:"
	@echo "juju destroy-environment $(JENV) -y"

.PHONY: unittest
unittest: $(VENV_ACTIVATE)
	$(NOSE) --verbosity 2 -s -w unit_tests \
		--with-coverage --cover-package hooks --cover-erase
