## Onboarded:
* [ansible-bender](https://github.com/ansible-community/ansible-bender/)
* [blivet-gui](https://github.com/storaged-project/blivet-gui)
* [conu](https://github.com/user-cont/conu)
* [did](https://github.com/psss/did)
* [dnf](https://github.com/rpm-software-management/dnf)
* [fmf](https://github.com/psss/fmf)
* [jose](https://github.com/latchset/jose)
* [libdnf](https://github.com/rpm-software-management/libdnf)
* [numactl](https://github.com/numactl/numactl/)
* [osbuild](https://github.com/osbuild/osbuild)
* [packit](https://github.com/packit-service/packit)
* [pycharm-community-edition](https://github.com/phracek/pycharm-community-edition)
* [python-avocado](https://github.com/avocado-framework/avocado)
* [python-deprecated](https://github.com/tantale/deprecated)
* [python-dockerfile-parse](https://github.com/containerbuildsystem/dockerfile-parse)
* [python-ogr](https://github.com/packit-service/ogr)
* [python-urlgrabber](https://github.com/rpm-software-management/urlgrabber)
* [rear](https://github.com/rear/rear/)
* [rebase-helper](https://github.com/rebase-helper/rebase-helper)
* [tmt](https://github.com/psss/tmt)
* [tmux-top](https://github.com/TomasTomecek/tmux-top)
* [tuned](https://github.com/redhat-performance/tuned)
* [sen](https://github.com/TomasTomecek/sen)

## In review(packit):
* chkconfig - https://github.com/fedora-sysv/chkconfig/pull/25
* conman - https://github.com/dun/conman/pull/33
* cronie - https://github.com/cronie-crond/cronie/pull/47
* Cython - https://github.com/cython/cython/pull/3229
* edd - https://github.com/psss/edd/pull/10
* initscripts - https://github.com/fedora-sysv/initscripts/pull/292
* initial-setup - https://github.com/rhinstaller/initial-setup/pull/79
* jansi-native - https://github.com/fusesource/jansi-native/pull/22
* libica - https://github.com/opencryptoki/libica/pull/33
* mod_security_crs - https://github.com/SpiderLabs/owasp-modsecurity-crs/pull/1621
* openssl-ibmca - https://github.com/opencryptoki/openssl-ibmca/pull/60
* python-meh - https://github.com/rhinstaller/python-meh/pull/21
* python-nitrate - https://github.com/psss/python-nitrate/pull/14
* python-paramiko - https://github.com/paramiko/paramiko/pull/1549
* python-pillow - https://github.com/python-pillow/Pillow/pull/4206
* python-requests - https://github.com/psf/requests/pull/5307
* python-simpleline - https://github.com/rhinstaller/python-simpleline/pull/62
* rpmdeplint - https://github.com/default-to-open/rpmdeplint/pull/1
* scap-security-guide - https://github.com/ComplianceAsCode/content/pull/5000
* scap-workbench - https://github.com/OpenSCAP/scap-workbench/pull/236
* sos - https://github.com/sosreport/sos/pull/1853
* tang - https://github.com/latchset/tang/pull/39

## In review(copr):
* cockpit-ostree - https://github.com/cockpit-project/cockpit-ostree/pull/31
* cockpit-podman - https://github.com/cockpit-project/cockpit-podman/pull/235

## Onboarded without copr builds
* nss-pem

## Blocked:
### Package not found
* cockpit-container
* redminecli

### Upstream not found
* anaconda-user-help

### Source in pagure
* standard-test-roles

### multiple sources or patches in spec
* avahi
* jzlib
* ksh
* libvncserver
* openscap
* pykickstart - has invalid packit.yml right now (spec.in in specfile path)
* python-requests
* rust-pretty-git-prompt - has packit config
* system-config-printer
* yp-tools

## Needs action for spec generate:
* anaconda - how is it built?
* abrt
* libreport
* cockpit - spec parse fails
* cockpit-composer - npm fails
* rpminspect - instructions for creating .spec?
* satyr

## Other error
* expat - unclosed macro or bad line continuation
* javapackages-tools - unclosed macro or bad line continuation
* gperftools - Failed to parse SPEC file
* abrt-java-connector - The target archive doesn't use a common extension
* libevent - The target archive doesn't use a common extension

## Rejected
* python-requests-file
  * increased maintanance cost by having .packit.yml file in repo
  * More info: https://github.com/dashea/requests-file/pull/14
* pyparted
  * increased maintanance cost by having .packit.yml file in repo
  * https://github.com/packit-service/packit-service/issues/46
  * https://github.com/packit-service/packit/issues/540
  * More info: https://github.com/dcantrell/pyparted/pull/66
* lorax
  * automation for Fedora and COPR should not depend on upstream changes
   or carrying your config file in our repositories.
  * More info: https://github.com/weldr/lorax/pull/878
* checkpolicy - https://github.com/SELinuxProject/selinux/pull/186
  * related also to **libsepol, libselinux, libsemanage, policycoreutils, secilc, mcstrans**
  * multiple components and multiple tarballs from one repository
  * the packages from the repo depend on each other (have to be taken care of/built in a specific order)
  * changes have potential to be accepted only on fedora fork
  https://github.com/fedora-selinux/selinux, changes on
  upstream need to be approved via mailing list
  * lack of trust caused by failed cooperation with other always ready project
* libguestfs collection of tools:
  * The project is using mailing lists for reviews, not GitHub pull requests
  * The request from them is that packit-service would react to branch pushes instead of PR changes
    * https://github.com/packit-service/packit-service/issues/239
  * libnbd is able to be onboarded: https://github.com/TomasTomecek/libnbd/pull/1
* Red Hat infra services team & github.com/redhat-performance
  * Some of the projects are on-board.
  * Problems:
    * ["Only collaborators can trigger packit."](https://github.com/packit-service/packit/issues/606)
    * ["More verbose packit service."](https://github.com/packit-service/packit-service/issues/243)
    * ["New Fedora release should not require projects to change packit.yaml"](https://github.com/packit-service/packit/issues/540)
* Open Source projects from [David Cantrell](https://github.com/dcantrell)
  * [Packit should take care of the complete upstream release process](https://github.com/dcantrell/pyparted/pull/66#issuecomment-555038520):
    * Create tarball, sign it and upload
  * Push to Fedora iff all CI tests pass for the respective tag.
  * Handle %changelog.
* beaker, restraint
  * multiple sources - some just need to be fetched from a remote URL
    * could be worked around with actions
  * only one tarball is from the current repo
  * using `git describe` doesn't work for them - should be turned off, we should check how tito does this
  * are using gerrit+jenkins atm (tito releasing), but want to switch to github
  * provide API for artifacts (spec, srpm, rpms) so they can be linted (rpmlint)
* dnf
  * cross-PR dependencies
    * short-term solution: enable adding a repository to the copr project via a PR comment
    * create SRPM from master branch of a dependency, if no dependency is specified
    * are using packit: 50 % of builds fail b/c of dependant projects & pull requests
  * they use a dedicated repo for tests
  * Current CI solution:
    * provisioning: container image: contains rpm builds of all the components with tests included
    * the container image is the input for the testing phase
    * they want to have a matrix with all the test cases: distribute the runs to the testing farm
  * another complete run should be then preformed with all packages built like if the PRs were merged
* Dusty & CoreOS
  * synced_files: src/ dest/ confusion
  * naming: source-git, propose-update
  * docs, source-git: finish the guide, show packit.yml
  * source-git patches: some files are not excluded (packit.yaml, spec file, downstream files) - configurable?
  * having packit.yaml in dist-git is confusing: we could have a "link" in dist-git which would point to a real location
  * validate packit yaml and halt if it's invalid
  * operate on a copy of a git repo: configurable?
  * trigger: new commit in a branch, action: build in a koji tag (and push to a d-g branch)
  * end goal: build certain upstream projects in a tag, release the tag to a stream & ostree repo
    * they want to use real koji builds - being able to yum install from a koji tag
    * push to a dedicated dist-git branch?
  * 5-10 projects
  * talk to Christian G
