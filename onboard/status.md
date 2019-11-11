## Onboarded:
* ansible-bender
* blivet-gui
* conu
* dnf
* fmf
* libdnf
* osbuild
* packit
* pycharm-community-edition
* python-avocado
* python-deprecated
* python-dockerfile-parse
* python-ogr
* rebase-helper
* tmt
* tmux-top

## In review(packit):
* initial-setup - https://github.com/rhinstaller/initial-setup/pull/79
* python-meh - https://github.com/rhinstaller/python-meh/pull/21
* python-simpleline - https://github.com/rhinstaller/python-simpleline/pull/62
* rpmdeplint - https://github.com/default-to-open/rpmdeplint/pull/1

## In review(copr):
* cockpit-ostree - https://github.com/cockpit-project/cockpit-ostree/pull/31
* cockpit-podman - https://github.com/cockpit-project/cockpit-podman/pull/235
* rear - https://github.com/rear/rear/pull/2274
* sen - https://github.com/TomasTomecek/sen/pull/150

## Blocked:

### Package not found
* cockpit-container
* redminecli

### Upstream not found
* anaconda-user-help

### Source in pagure
* standard-test-roles

### multiple sources or patches in spec
* ksh
* pykickstart - has invalid packit.yml right now (spec.in in specfile path)
* rust-pretty-git-prompt - has packit config

## Needs action for spec generate:
* anaconda - how is it built?
* cockpit-composer - npm fails
* rpminspect - instructions for creating .spec?
* cockpit - spec parse fails

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
