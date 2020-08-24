mkdir --mode=0700 -p "${HOME}/.ssh"
pushd "${HOME}/.ssh"
install -m 0400 /my-ssh/id_rsa .
install -m 0400 /my-ssh/id_rsa.pub .
ssh-keyscan git.stg.centos.org >>known_hosts
popd

python3 onboard.py
