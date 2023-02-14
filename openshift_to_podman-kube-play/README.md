# How to make packit-service-tests-openshift OpenShift-less?

The way we run the [packit-service-tests-openshift](https://github.com/packit/packit-service/blob/eb5d95cdc1c1531ac27cc8dd5999ae310b06f2c5/.zuul.yaml#L21)
via `oc cluster up` was added a long time ago
([a3f5336](https://github.com/packit/packit-service/commit/a3f5336c49e18227ccabce55e32f95dc86eb03b7),
[11ca8d5](https://github.com/packit/packit-service/commit/11ca8d5b3557901fb478cfb1b5236eed30d7afb0))
and has been pretty much used the same way since then. The solution has some limitations, like:

- the cluster takes a long time to start
- it's Openshift v3
- requires docker
- [runs on centos-7 node](https://github.com/packit/packit-service-zuul/blob/386ef8a8e850f4ea2d6a0a055968ad069ec7d75d/zuul.d/jobs.yaml#L55)
  which has ansible-2.9, which we [need to stay compatible with](https://github.com/packit/deployment/pull/449#issuecomment-1425734576)

Do we really need a full-blown OpenShift to run these tests? Wouldn't a few containers do the trick as well?
I think the tests need to run just the `worker`, `service`, `postgres` and probably `redis`.
Then [there are](https://github.com/packit/packit-service/blob/main/files/check-inside-openshift.yaml)
a few extra volumes, pods and jobs.
IMHO nothing which couldn't be done directly on the node with podman.

There are a few ways how to orchestrate them:

- "manually" with `podman pod`, `podman volume`, `podman run`, etc. everything - should work, but isn't there an easier way?
- [`podman-compose` / `docker-compose`](https://www.redhat.com/sysadmin/podman-compose-docker-compose) - we already have [docker-compose.yml](https://github.com/packit/packit-service/blob/main/docker-compose.yml) so we're half-way there
- `podman kube play`- wait, what's that?

With `podman kube play` you give podman your existing k8s/openshift workloads
in YAML and podman "deploys" them to your local machine (instead of to a cluster).

    $ git clone https://github.com/packit/deployment.git
    $ cd deployment/openshift
    $ podman kube play redis.yml
    Volumes:
    redis-pvc
    Pod:
    3724c8a13a4167649be482b74b4c29c406eff39f1f13a0e7aa626f4b748bc37b
    Container:
    2f65ece7e362b580b5f4b4ca356f1e346ad38e40cde677c30a7021b766ad75ab

    $ podman ps
    2f65ece7e362  quay.io/sclorg/redis-6-c9s:latest    run-redis   28 seconds ago  Up 28 seconds  0.0.0.0:6379->6379/tcp  redis-pod-redis

    $ podman kube down redis.yml
    Pods stopped:
    3724c8a13a4167649be482b74b4c29c406eff39f1f13a0e7aa626f4b748bc37b
    Pods removed:
    3724c8a13a4167649be482b74b4c29c406eff39f1f13a0e7aa626f4b748bc37b

There's also an [ansible module](https://docs.ansible.com/ansible/latest/collections/containers/podman/podman_play_module.html) for it.

You can also [run it as a systemd service](https://www.redhat.com/sysadmin/kubernetes-workloads-podman-systemd)

    $ cd deployment/openshift
    $ escaped=$(systemd-escape `pwd`/redis.yml)
    $ systemctl --user start podman-kube@$escaped.service
    $ systemctl --user status podman-kube@$escaped.service
    ● podman-kube@-home-jpopelka-git-packit-deployment-openshift-redis.yml.service - A template for running K8s workloads via podman-kube-play
         Loaded: loaded (/usr/lib/systemd/user/podman-kube@.service; disabled; preset: disabled)
         Active: active (running) since Tue 2023-02-14 17:55:23 CET; 7s ago
           Docs: man:podman-kube-play(1)
       Main PID: 78308 (podman)
          Tasks: 31 (limit: 38173)
         Memory: 29.9M
            CPU: 380ms
         CGroup: /user.slice/user-1000.slice/user@1000.service/app.slice/app-podman\x2dkube.slice/podman-kube@-home-jpopelka-git-packit-deployment-openshift-redis.yml.service
                 ├─78308 /usr/bin/podman kube play --replace --service-container=true /home/jpopelka/git/packit/deployment/openshift/redis.yml

    $ podman ps
    340d065ba1eb  quay.io/sclorg/redis-6-c9s:latest     run-redis   2 minutes ago  Up 2 minutes  0.0.0.0:6379->6379/tcp  redis-pod-redis

    $ systemctl --user stop podman-kube@$escaped.service
