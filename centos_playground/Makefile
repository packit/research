build-onboard:
	podman build . -t centos-onboard -f onboard/Containerfile

run-onboard:
	podman run --rm --cap-add=SYS_ADMIN \
	-v ${HOME}/.ssh/:/my-ssh/ \
	-v ${PWD}/onboard/input/:/in \
	-e PAGURE_TOKEN=${PAGURE_TOKEN} \
	-e GITLAB_TOKEN=${GITLAB_TOKEN} \
	centos-onboard
