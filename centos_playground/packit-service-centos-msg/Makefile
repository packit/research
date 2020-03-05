IMAGE ?= usercont/packit-service-centos-msg:dev
CONTAINER_ENGINE ?= docker
ANSIBLE_PYTHON ?= /usr/bin/python3
AP ?= ansible-playbook -vv -c local -i localhost, -e ansible_python_interpreter=$(ANSIBLE_PYTHON)

build: files/install-deps.yaml files/recipe.yaml
	$(CONTAINER_ENGINE) build --rm -t $(IMAGE) .

# run 'make build' first
# copy (symlink) fedora.toml from our packit-service@gitlab repo into this dir
run:
	$(CONTAINER_ENGINE) run --rm \
        -v /home/sakalosj/projects/secrets/secrets/stg:/secrets \
        -e CENTOS_CA_CERTS="/secrets/centos-server-ca.cert" \
        -e CENTOS_CERTFILE="/secrets/centos.cert" \
		$(IMAGE)
