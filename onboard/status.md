## Onboarded:
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
* blivet-gui - https://github.com/storaged-project/blivet-gui/pull/135
* ansible-bender - https://github.com/ansible-community/ansible-bender/pull/173
* initial-setup - https://github.com/rhinstaller/initial-setup/pull/79
* lorax - https://github.com/weldr/lorax/pull/878
* python-meh - https://github.com/rhinstaller/python-meh/pull/21
* python-simpleline - https://github.com/rhinstaller/python-simpleline/pull/62
* rpmdeplint - https://github.com/default-to-open/rpmdeplint/pull/1

## In review(copr):
* sen - https://github.com/TomasTomecek/sen/pull/150

## Onboarded without copr builds yet
* cockpit-ostree
* cockpit-podman
* rear
* redminecli
* rust-pretty-git-prompt

## Blocked:
### package not found
* cockpit-container
* redminecli

### Upstream not found
* anaconda-user-help

### Source in pagure
* standard-test-roles

## Needs action for spec generate:
* anaconda
* cockpit-composer
* ksh
* rpminspect
* cockpit
* pykickstart - has invalid packit.yml right now (spec.in in specfile path)

## Rejected
* python-requests-file
  * increased maintanance cost by having .packit.yml file in repo
  * More info: https://github.com/dashea/requests-file/pull/14
* pyparted
  * increased maintanance cost by having .packit.yml file in repo
  * https://github.com/packit-service/packit-service/issues/46
  * https://github.com/packit-service/packit/issues/540
  * More info: https://github.com/dcantrell/pyparted/pull/66
