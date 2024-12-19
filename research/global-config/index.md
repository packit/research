---
title: Global configuration
authors:
  - mmassari
sidebar_position: 1
---

You can customize the service configuration for a user project in two different ways:

1. There is a configuration on the service side which has to be updated by the service team (upon notification from the service users for opt-in or opt-out from the service). This is how you can enable or disable Zuul for the Fedora CI nowadays: .
   I will refer to this solution as a **top-down solution**.
2. There is a configuration, related with the service, on the user's project side. This is how packit works today. I will refer to this solution as a **bottom-up solution**.

You can configure services for individual projects in two ways:

1. Top-Down solution: configuration resides on the service side, managed by the service team. Users notify the team to opt in or out. Example: Zuul for Fedora CI uses this approach ([configuration reference](https://pagure.io/fedora-project-config/blob/master/f/resources/fedora-distgits.yaml)).

2. Bottom-Up solution: configuration lives in the user's project repository. Packit currently implements this approach.

The top-down approach represents a global configuration, while the bottom-up solution can reference global or semi-global configurations. Let's analyze both approaches.

# Top-Down solution

The service side maintains project-specific behavior configurations.

## Advantages

- Users don't need configuration files in their projects; they might not like the idea of having a service related file in their projects.
- Configuration migrations are straightforward for the service team; it is just a change in a file that belongs to the team.
- Highest performance due to direct configuration access; no need to load and pre-process other files.
- Quickest implementation; this approach is the same as for the packit-service configuration file.

## Disadvantages

- It is probably easier, for the final user, to look for the service configuration file in its own repo instead of a service repo.
- Less user engagement due to limited visibility of configuration changes. Even though a configuration migration can be simpler for the service team it could be less explicit for the final user. Being able to change behaviour without the user acknowledging it could not be a good idea. In packit there already is a configuration migration script.
- The global configuration file could really grow huge and be difficult to maintain both for the service team and for a final user that wants to contribute to it.
- Lacks ecosystem-specific configuration management. There is no encapsulation for "middle layer" knowledge, no easy way to manage ecosystem configurations. Configurations could be grouped in different nodes with different defaults but there is no easy way, for the service team, to know if the user who is asking to update a configuration has the rights for doing so.
- Differs from Packit's current approach, potentially confusing users. This could work mainly for the _Fedora CI_ and could confuse users that use the standard packit configuration for _upstream continuous integration_ and _release synchronization_.

# Bottom-Up solution

Project-side configuration with ability to reference global configurations.

## Advantages

- User-friendly and explicit. Everything is on the user side (more quick for him) and the file will never grow too much because of other project details.
- Flexible customization through layered configurations and better ecosystem-specific configuration support.
- Consistent with current Packit implementation.

## Disadvantages

- More complex configuration migrations because they are on the user side.
- Additional processing overhead. It will require time to load multiple configuration layers.
- Requires implementation of inheritance/templating mechanisms.

## Configuration Layers

### Service-Side Layer

The last layer of a configuration chain could be on the service side and it could be referenced in a sort of opt-in mechanism or it could be automatically applied.

### User-Side Layer

At the moment the packit service needs just one configuration file on the user project side both for the **upstream continuous integration** and for the **release synchronization**.
When implementing the **Fedora CI** (which is a _downstream continuous integration_) a new configuration file could be required or the configuration can be merged with the existing one.

## Configurations chain implementation

There could be different ways for managing configuration relationships, I will analyse three of them:

- templating
- global configuration + overlays
- inheritance

### 1. Templating

#### https://github.com/packit/templeates/config/simple-pull-from-upstream.yaml.j2

```yml
# Packit pull-from-upstream config
specfile_path: { { specfile_path } }

upstream_package_name: { { upstream_package_name } }
downstream_package_name: { { downstream_package_name } }
upstream_project_url: { { upstream_package_url } }
upstream_tag_template: v{version}

jobs:
  - job: pull_from_upstream
    trigger: release
    dist_git_branches:
      - fedora-rawhide
  - job: koji_build
    trigger: commit
    allowed_pr_authors: ["packit", { { allowed_pr_authors } }]
    dist_git_branches:
      - fedora-rawhide
```

#### https://gitlab.gnome.org/packit/templates/configs/gnome-tests.yaml.j2

```yml
# Gnome default tests config
jobs:
  - job: tests
    trigger: pull_request
    packages: [{{ downstream_package_name }}]
    tmt_plan: "smoke|full|packit-integration|{{ tmt_other_plans }}"
    targets:
      - fedora-rawhide
  {% if tests_on_commit %}
  - job: tests
    trigger: commit
    packages: [{{ downstream_package_name }}]
    tmt_plan: "smoke|full|packit-integration|{{ tmt_other_plans }}"
    targets:
      - fedora-rawhide
  {% endif %}
```

#### https://gitlab.gnome.org/package/packit.yaml

```yml
# A gnome package packit config
templates:
  - https://github.com/packit/templeates/config/simple-pull-from-upstream.yaml.j2
    vars:
      specfile_path: specfile_path
      upstream_package_name: upstream_package_name
      downstream_package_name: downstream_package_name
      upstream_project_url: upstream_project_url
      allowed_pr_authors: allowed_pr_authors
  - https://gitlab.gnome.org/packit/templates/configs/gnome-tests.yaml.j2
      downstream_package_name: downstream_package_name
      tmt_other_plans: tmt_other_plans
      tests_on_commit: false
```

### 2. Global config + overlay

#### https://github.com/packit/templates/configs/standard-pull-from-upstream.yaml.j2

```yml
# Packit pull-from-upstream config
specfile_path: { { specfile_path } }

upstream_package_name: { { upstream_package_name } }
downstream_package_name: { { downstream_package_name } }
upstream_project_url: { { upstream_package_url } }
upstream_tag_template: v{version}

jobs:
  - job: pull_from_upstream
    trigger: release
    dist_git_branches:
      - fedora-rawhide
  - job: koji_build
    trigger: commit
    allowed_pr_authors: ["packit", { { allowed_pr_authors } }]
    dist_git_branches:
      - fedora-rawhide
```

#### https://gitlab.gnome.org/packit/templates/configs/default_packit.yaml.j2

```yml
# Gnome default packit config
config:
  base: https://github.com/packit/templates/configs/standard-pull-from-upstream.yaml.j2
  values:
    allowed_pr_authors: gnome-admins

jobs:
  - job: tests
    trigger: pull_request
    packages: [{{ downstream_package_name }}]
    tmt_plan: "smoke|full|packit-integration|{{ tmt_other_plans }}"
    targets:
      - fedora-rawhide
  {% if tests_on_commit %}
  - job: tests
    trigger: commit
    packages: [{{ downstream_package_name }}]
    tmt_plan: "smoke|full|packit-integration|{{ tmt_other_plans }}"
    targets:
      - fedora-rawhide
  {% endif %}
```

#### https://gitlab.gnome.org/package/packit.yaml

```yml
# A gnome package packit config
config:
  base: https://gitlab.gnome.org/packit/templates/configs/default_packit.yaml.j2
  values:
    specfile_path: specfile_path
    upstream_package_name: upstream_package_name
    downstream_package_name: downstream_package_name
    upstream_project_url: upstream_package_url
    tmt_other_plans: package-tests
    tests_on_commit: false
```

### 3. Inheritance

#### https://github.com/packit/templates/configs/standard-pull-from-upstream.yaml

```yml
# Packit pull-from-upstream config
specfile_path: -OVERRIDE ME-

upstream_package_name: -OVERRIDE ME-
downstream_package_name: -OVERRIDE ME-
upstream_project_url: -OVERRIDE ME-

upstream_tag_template: v{version}

jobs:
  - job: pull_from_upstream
    trigger: release
    dist_git_branches:
      - fedora-rawhide
  - job: koji_build
    trigger: commit
    allowed_pr_authors: ["packit"]
    dist_git_branches:
      - fedora-rawhide
```

#### https://gitlab.gnome.org/packit/templates/configs/default_packit.yaml

```yml
# Gnome default packit config
inherit: https://github.com/packit/templates/configs/standard-pull-from-upstream.yaml

jobs:
  - job: koji_build
    allowed_pr_authors: ["packit", "gnome-admins"]

  - job: tests
    trigger: pull_request
    tmt_plan: "smoke|full|packit-integration"
    targets:
      - fedora-rawhide
```

#### https://gitlab.gnome.org/package/packit.yaml

```yml
# A gnome package packit config
inherit: https://gitlab.gnome.org/packit/templates/configs/default_packit.yaml

specfile_path: specfile_path
upstream_package_name: upstream_package_name
downstream_package_name: downstream_package_name
upstream_project_url: upstream_package_url

jobs:
  - job: tests
    packages: ["downstream_package_name"]
    tmt_plan: "smoke|full|packit-integration|package-tests"
```

### PROs and CONs

#### Templating

##### Pros

Flexible, probably the most flexible implementation that allows to freely mix configuration snippets for creating a customized final configuration.

##### Cons

The "pure" templating mechanism, in the above example, requires the package maintainer to know that koji builds, in the gnome ecosystem, should be allowed for any **gnome-admin**, instead _inheritance_ and _global config + overlays_ encapsulate well the knowledge in the middle layer packit config.

Templating is flexible but on the other end it is more error prone; there is no _base configuration_ and a packager can list templates in the wrong order.

Probably, in the end, the packager will use smaller config snippets, decreasing performance and readability.

#### Global config + overlays

##### Pros

Good knowledge encapsulation in middle layers (see the **gnome-admin** for allowed_pr_authors in the above example).

Explicit and thus easily readable, since the use of templating.

Flexible, config snippets can easily be removed using template conditional functionalities (as in the above example for the test job with trigger commit).

##### Cons

The templating syntax can be more error prone if compared with inheritance.

#### Inheritance

##### Pros

Concise, it's the most concise syntax we could use and probably the least error prone.

##### Cons

Poor flexibility, I don't see an easy way to disable the above test job with trigger commit.

Not really explicit, even though we use a placeholder it is harder to recognize the keys that need overriding.

### Implementation

Personally I find the _global config + overlays_ approach the best and in this case we would need to:

- add the following keys to the `PackageConfig` class:

```yml
config:
  base: https://gitlab.gnome.org/packit/templates/configs/default_packit.yaml.j2
  values: ...
```

- load the packit.yaml file and search for the `config` key in it. If a `config` key is found we need to **recursively** look for the _base config_ and start processing all the templates in the chain, creating a new temporary packit.yml that will be used instead of the original one.
  I see this code tied with the `LocalProject` class but I can be wrong.
  We should make the new code work both for the packit CLI and the packit-service. Thinking at packit CLI, we should probably stay flexible and let the `base: URI` be also a local url (like `file:///`).

- let the user know what the final configuration looks like (both for CLI and service).

#### Jinja2 vs Ansible library

For template management I would probably just use the **jinja2 template library**, even though we can also think about the ansible library.
The ansible library could let us use `built-in filters and functions` but I don't see use cases for them and as a cons it has a heavier dependency footprint.

### Performances

Splitting the configuration in multiple configuration files will lead obviously to worst performance. Personally I don't see a way to prevent it.

We can limit the number of recursion steps; 3/4 steps are, from my point of view, more than enough. Having a recursion limit will avoid an infinite recursion for malformed configurations.

### packit-service defaults

It could happen that the packit-service config defaults for the "Fedora CI instance" and those for the "Usual instance" (as an example) diverge.

If it happens we could create two _hidden_, _inner_ packit config bases, one per instance, which will always be used for merging any packit config we process; in this way the differences will be grouped explicitly in a single place and we could, probably, enable and disable jobs for one instance or the other (as an example `pull-from-upstream` should not appear in fedora ci packit configuration) just using templating.

<!--
We already have a configuration file that enables packit we can still count on it.

- it could work for all packit instances:
  - upstream ci + downstream sync experience
  - downstream ci
    We already have a mixed experience for upstream ci and downstream sync, from an user point of view it makes no much sense to split the downstream ci configuration because it runs on a different packit service instance.
    If we want to have a different configuration for the downstream ci probably we should think about splitting configurations for different users experiences?
  - upstream ci
  - downstream ci
  - sync release

Or we can have just one packit config

- by default one project in distgit with the packit config would be enabled the downstream CI and for this reason we should probably have a key to be able to opt-out from it (both as a user action or as a packit configuration action) we can achive it using the above template mechanism and always apply out default to a user configuration.
  Or **the CI experience will be anabled if the user refers the related global config**.
  However if the user configuration is against the will of our configuration we should decide which configuration wins (I would say ours)
- it should be visible which is the result of applying the user packit config to a packit instance config. So we should probably have a command line or a packit service command to show the user the resulting configuration.
-->
