build-onboard:
	podman build . -t centos-onboard -f onboard/Containerfile

run-onboard:
	podman run --cap-add=SYS_ADMIN \
	-v ${HOME}/.ssh/:/my-ssh/ \
	-v ${PWD}/onboard/input/:/in \
	-e PAGURE_TOKEN=${PAGURE_TOKEN} \
	centos-onboard
