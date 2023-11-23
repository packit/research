---
title: Research Openshift tests in Zuul alternatives
authors: mmassari
---

This research is about giving an answer to [this card](https://github.com/orgs/packit/projects/7/views/1?pane=issue&itemId=43441287).

## Openshift tests using podman kube play

Following suggestions in [this research](https://packit.dev/research/testing/openshift-to-podman-kube-play) I have done a quick & dirty setup for running _packit-service openshift tests_ using pods created with `podman kube play`.

### Quick and dirty steps for make them running

#### 1. We need to convert jinja templates in pure yaml files

This is a **dirty** ansible playbook for doing it

```yaml
# ansible-playbook -vv -c local -i localhost render_templates.yaml
---
- name: Render jinja2 templates
  hosts: localhost
  vars:
    validate_certs: true
    service: "{{ lookup('env', 'SERVICE') | default('packit', True) }}"
    deployment: "dev"
    tenant: packit # MP+ tenant
    with_tokman: true
    with_fedmsg: true
    with_redis_commander: false
    with_flower: false
    with_dashboard: true
    with_beat: true
    with_pushgateway: true
    with_repository_cache: false
    repository_cache_storage: 4Gi
    push_dev_images: false
    with_fluentd_sidecar: false
    postgres_version: 13
    image: quay.io/packit/packit-service:{{ deployment }}
    image_worker: quay.io/packit/packit-worker:{{ deployment }}
    image_fedmsg: quay.io/packit/packit-service-fedmsg:{{ deployment }}
    image_dashboard: quay.io/packit/dashboard:{{ deployment }}
    image_tokman: quay.io/packit/tokman:{{ deployment }}
    image_fluentd: quay.io/packit/fluentd-splunk-hec:latest
    # project_dir is set in tasks/project-dir.yml
    path_to_secrets: "{{ project_dir }}/secrets/{{ service }}/{{ deployment }}"
    # to be used in Image streams as importPolicy:scheduled value
    auto_import_images: "{{(deployment != 'prod')}}"
    # used in dev/zuul deployment to tag & push images to cluster
    # https://github.com/packit/deployment/issues/112#issuecomment-673343049
    # container_engine: "{{ lookup('pipe', 'command -v podman 2> /dev/null || echo docker') }}"
    container_engine: docker
    celery_app: packit_service.worker.tasks
    celery_retry_limit: 2
    celery_retry_backoff: 3
    workers_all_tasks: 1
    workers_short_running: 0
    workers_long_running: 0
    distgit_url: https://src.fedoraproject.org/
    distgit_namespace: rpms
    sourcegit_namespace: "" # fedora-source-git only
    pushgateway_address: http://pushgateway
    # Check that the deployment repo is up-to-date
    check_up_to_date: true
    # Check that the current vars file is up-to-date with the template
    check_vars_template_diff: true
    deployment_repo_url: https://github.com/packit/deployment.git
    # used by a few tasks below
    k8s_apply: false
    tokman:
      workers: 1
      resources:
        requests:
          memory: "88Mi"
          cpu: "5m"
        limits:
          memory: "128Mi"
          cpu: "50m"
    appcode: PCKT-002
    project: myproject
    host: https://api.crc.testing:6443
    api_key: ""
    validate_certs: false
    check_up_to_date: false
    push_dev_images: false # pushing dev images manually!
    check_vars_template_diff: false
    with_tokman: false
    with_fedmsg: false
    with_redis_commander: false
    with_flower: false
    with_beat: false
    with_dashboard: false
    with_pushgateway: false
    with_fluentd_sidecar: false
    managed_platform: false
    workers_all_tasks: 1
    workers_short_running: 0
    workers_long_running: 0
    path_to_secrets: "{{ project_dir }}/secrets/{{ service }}/{{ deployment }}"
    sandbox_namespace: "packit-dev-sandbox"
    packit_service_project_dir: "/home/maja/PycharmProjects/packit-service"
  tasks:
  - include_tasks: tasks/project-dir.yml
  - name: include variables
    ansible.builtin.include_vars: "{{ project_dir }}/vars/{{ service }}/{{ deployment }}.yml"
    tags:
      - always

  - name: Getting deploymentconfigs
    include_tasks: tasks/set-facts.yml
    tags:
      - always

  - name: Include extra secret vars
    ansible.builtin.include_vars:
      file: "{{ path_to_secrets }}/extra-vars.yml"
      name: vault
    tags:
      - always

    # to be able to read the github_app_id from the configuration file in tokman
  - name: include packit-service configuration
    ansible.builtin.include_vars:
      file: "{{ path_to_secrets }}/packit-service.yaml"
      name: packit_service_config
    tags:
      - tokman

  - name: include extra secret vars
    ansible.builtin.include_vars: "{{ path_to_secrets }}/extra-vars.yml"
    tags:
      - always


  - name: render templates
    ansible.builtin.template:
       src: "{{ project_dir }}/openshift/redis.yml.j2"
       dest: /tmp/redis.yaml
  - name: render templates
    ansible.builtin.template:
       src: "{{ project_dir }}/openshift/postgres.yml.j2"
       dest: /tmp/postgres.yaml
  - name: render templates
    ansible.builtin.template:
       src: "{{ project_dir }}/openshift/packit-service.yml.j2"
       dest: /tmp/packit-service.yaml
  - name: render templates
    vars:
      component: packit-worker
      queues: "short-running,long-running"
      worker_replicas: "1"
      worker_requests_memory: "384Mi"
      worker_requests_cpu: "100m"
      worker_limits_memory: "1024Mi"
      worker_limits_cpu: "400m"
    ansible.builtin.template:
       src: "{{ project_dir }}/openshift/packit-worker.yml.j2"
       dest: /tmp/packit-worker.yaml
  - name: render postgres templates
    ansible.builtin.template:
       src: "{{ project_dir }}/openshift/secret-postgres.yml.j2"
       dest: /tmp/secret-postgres.yaml
  - name: render packit-secrets templates
    ansible.builtin.template:
       src: "{{ project_dir }}/openshift/secret-packit-secrets.yml.j2"
       dest: /tmp/secret-packit-secrets.yaml
  - name: render packit-config templates
    ansible.builtin.template:
       src: "{{ project_dir }}/openshift/secret-packit-config.yml.j2"
       dest: /tmp/secret-packit-config.yaml
  - name: render secret sentry templates
    ansible.builtin.template:
       src: "{{ project_dir }}/openshift/secret-sentry.yml.j2"
       dest: /tmp/secret-sentry.yaml
  - name: render secret splunk templates
    ansible.builtin.template:
       src: "{{ project_dir }}/openshift/secret-splunk.yml.j2"
       dest: /tmp/secret-splunk.yaml
  - name: render secret ssh templates
    ansible.builtin.template:
       src: "{{ project_dir }}/openshift/secret-packit-ssh.yml.j2"
       dest: /tmp/secret-packit-ssh.yaml
  - name: render secret aws templates
    ansible.builtin.template:
       src: "{{ project_dir }}/openshift/secret-aws.yml.j2"
       dest: /tmp/secret-aws.yaml
```

#### 2. Tweak the generated yaml files and play our main pods locally

We are now able to run redis, postgres, service and worker locally using the Openshift configuration files and podman kube play.

```bash
podman kube play /tmp/redis.yaml
podman kube play /tmp/secret-postgres.yaml
podman kube play /tmp/postgres.yaml
podman kube play /tmp/secret-packit-secrets.yaml
podman kube play /tmp/secret-packit-config.yaml
podman kube play /tmp/secret-sentry.yaml
podman kube play /tmp/secret-splunk.yaml
podman kube play --replace /tmp/packit-service.yaml
podman kube play /tmp/secret-packit-ssh.yaml
podman kube play /tmp/secret-aws.yaml
sed -i "s/resources:/securityContext:\n            runAsUser: 1024\\n            runAsNonRoot: true\\n          resources:/" /tmp/packit-service.yaml
sed -i "s/StatefulSet/Deployment/" /tmp/packit-worker.yaml
sed -i "s/resources:/securityContext:\n            runAsUser: 1024\\n            runAsNonRoot: true\\n          resources:/" /tmp/packit-worker.yaml
podman kube play --replace /tmp/packit-worker.yaml
```

#### 3. Run openshift packit-service tests locally

Apply this patch to packit-service repo **adjusting** in it the `hostPath` to where the packit-service repo is:

```diff
diff --git a/files/test-in-openshift.yaml b/files/test-in-openshift.yaml
index 0d555a13..2740aa4b 100644
--- a/files/test-in-openshift.yaml
+++ b/files/test-in-openshift.yaml
@@ -1,9 +1,12 @@
 ---
-kind: Job
-apiVersion: batch/v1
+kind: Deployment
+apiVersion: apps/v1
 metadata:
   name: packit-tests
 spec:
+  replicas: 1
+  strategy:
+    type: Recreate
   template:
     spec:
       volumes:
@@ -12,10 +15,13 @@ spec:
         - name: packit-config
           secret: { secretName: packit-config }
         - name: test-src-pv
-          persistentVolumeClaim: { claimName: test-src-pvc }
+          hostPath:
+            path: "/home/maja/PycharmProjects/packit-service/"
+            type: Directory
+              #persistentVolumeClaim: { claimName: test-src-pvc }
         - name: test-data-pv
           persistentVolumeClaim: { claimName: test-data-pvc }
-      restartPolicy: Never
+            #restartPolicy: Never
       containers:
         - name: packit-tests
           image: quay.io/packit/packit-service-tests:stg
@@ -41,11 +47,15 @@ spec:
             - name: packit-config
               mountPath: /home/packit/.config
             - name: test-src-pv
-              mountPath: /src
+              mountPath: /src:Z
             - name: test-data-pv
               mountPath: /tmp/test_data
-          command: ["bash", "/src/files/run_tests.sh"]
-  backoffLimit: 1
+          #privileged: true
+          #securityContext:
+          #  runAsUser: 1024
+          #  runAsNonRoot: true
+          command: ["/bin/bash"]
+          args: ["-c", "sleep 1800"]
 ---
 kind: PersistentVolumeClaim
 apiVersion: v1
diff --git a/files/test-src-mounter.yaml b/files/test-src-mounter.yaml
index 20ec681b..297064a5 100644
--- a/files/test-src-mounter.yaml
+++ b/files/test-src-mounter.yaml
@@ -13,6 +13,6 @@ spec:
     - name: packit-tests
       image: quay.io/packit/packit-service-tests:stg
       volumeMounts:
-        - mountPath: /src
+        - mountPath: /home/maja/PycharmProjects/packit-service/
           name: test-src-pv
       command: ["bash", "-c", "sleep 10000"]
```

Now you can run the packit-service openshift tests using podman kube instead of starting the _service_ and the _worker_; remember of running a `podman kube play --down /tmp/xxx.yaml` for every line above where you have used `podman kube play /tmp/xxx.yaml`

```bash
podman kube play /tmp/redis.yaml
podman kube play /tmp/secret-postgres.yaml
podman kube play /tmp/postgres.yaml
podman kube play /tmp/secret-packit-secrets.yaml
podman kube play /tmp/secret-packit-config.yaml
podman kube play --replace /home/maja/PycharmProjects/packit-service/files/test-src-mounter.yaml
podman kube play --replace /home/maja/PycharmProjects/packit-service/files/test-in-openshift-get-data.yaml
podman kube play --replace /home/maja/PycharmProjects/packit-service/files/test-in-openshift.yaml
podman exec -ti packit-tests-pod-packit-tests /bin/bash
sh /src/files/run_tests.sh
```

There will be two failing tests:

```
============================================== short test summary info ===============================================
FAILED tests_openshift/openshift_integration/test_pkgtool.py::Pkgtool::test_pkgtool_clone - requre.exceptions.ItemNotInStorage: Keys not in storage:/src/tests_openshift/openshift_integration/test_data/test...
FAILED tests_openshift/openshift_integration/test_sandcastle.py::test_get_api_client - kubernetes.config.config_exception.ConfigException: Invalid kube-config file. No configuration found.
========================== 2 failed, 172 passed, 3 skipped, 37 warnings in 70.40s (0:01:10) ==========================
```

I think the first one can be fixed improving this setup but not the second one:

```python
________________________________________________ test_get_api_client _________________________________________________

    def test_get_api_client():
        """let's make sure we can get k8s API client"""
>       assert sandcastle.Sandcastle.get_api_client()

tests_openshift/openshift_integration/test_sandcastle.py:9:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
/usr/local/lib/python3.9/site-packages/sandcastle/api.py:324: in get_api_client
    load_kube_config(client_configuration=configuration)
/usr/local/lib/python3.9/site-packages/kubernetes/config/kube_config.py:792: in load_kube_config
    loader = _get_kube_config_loader(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

filename = '~/.kube/config', config_dict = None, persist_config = True
kwargs = {'active_context': None, 'config_persister': <bound method KubeConfigMerger.save_changes of <kubernetes.config.kube_config.KubeConfigMerger object at 0x7ff3a1ea7d30>>}
kcfg = <kubernetes.config.kube_config.KubeConfigMerger object at 0x7ff3a1ea7d30>

    def _get_kube_config_loader(
            filename=None,
            config_dict=None,
            persist_config=False,
            **kwargs):
        if config_dict is None:
            kcfg = KubeConfigMerger(filename)
            if persist_config and 'config_persister' not in kwargs:
                kwargs['config_persister'] = kcfg.save_changes

            if kcfg.config is None:
>               raise ConfigException(
                    'Invalid kube-config file. '
                    'No configuration found.')
E               kubernetes.config.config_exception.ConfigException: Invalid kube-config file. No configuration found.

/usr/local/lib/python3.9/site-packages/kubernetes/config/kube_config.py:751: ConfigException
```

## Summary

[`podman kube play`](https://docs.podman.io/en/v4.4/markdown/podman-kube-play.1.html) can not be used to test:

- _sandcastle_; we need a k8s cluster to be able to use the `kubernates` library. We could deploy pods in the cluster using [`podman kube apply`](https://docs.podman.io/en/v4.4/markdown/podman-kube-apply.1.html) but still we need an up and running cluster.
- _deployment_; the Openshift tests in the _deployment_ repo are checking that pods are up and running on an Openshift dev instance; we can not check the same using `podman kube play` or `podman kube apply` (we would test different deployment settings...).

`podman kube play` can be used for openshift tests in _packit-service_ project not related with _sandcastle_ but `docker-compose` should be enough for these as well; so I don't really see advantages in using `podman kube play`.

For tests in _deployment_, _sandcastle_ and in _packit-service_ (which reference _sandcastle_) we still need a running k8s cluster.

If I get it correctly, the **strimzi** project has tests running on Testing Farm using _minikube_: https://developers.redhat.com/articles/2023/08/17/how-testing-farm-makes-testing-your-upstream-project-easier#
For this reason I think we can probably make something similar using Openshift (maybe using Openshift Local - I think it makes sense to test everything against an Openshift instance).
