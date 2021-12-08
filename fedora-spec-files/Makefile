.PHONY = build run generate-data
IMAGE_NAME := fedora-spec-research
PODMAN_RUN_THIS_DIR := podman run --rm -v $(CURDIR):/fedora-spec-files:Z -w /fedora-spec-files

# build the container image with the jupyter notebook and all the dependencies
build:
	podman build --tag=$(IMAGE_NAME) .

# run jupyter notebook
run:
	$(PODMAN_RUN_THIS_DIR) --net=host -it $(IMAGE_NAME) jupyter notebook --allow-root ./fedora-spec-files.ipynb

rpm-specs-latest.tar.xz:
	curl -LO https://src.fedoraproject.org/repo/rpm-specs-latest.tar.xz

rpm-specs: rpm-specs-latest.tar.xz
	tar -xf $(CURDIR)/rpm-specs-latest.tar.xz

# Run the data collection tooling and generate data.json
generate-data: rpm-specs
	$(PODMAN_RUN_THIS_DIR) $(IMAGE_NAME) ./generate-data.py
