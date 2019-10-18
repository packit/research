## Onboarded:
* tmux-top
* osbuild
* packit
* python-ogr
* ...

## In review(packit):
* pyparted - https://github.com/dcantrell/pyparted/pull/66 (!) needs answers 
* python-meh - https://github.com/rhinstaller/python-meh/pull/21
* python-simpleline - https://github.com/rhinstaller/python-simpleline/pull/62
* anaconda-user-help - https://github.com/storaged-project/blivet-gui/pull/135
* initial-setup - https://github.com/rhinstaller/initial-setup/pull/79
* lorax - https://github.com/weldr/lorax/pull/878
* python-requests-file - https://github.com/dashea/requests-file/pull/14
* ansible-bender - https://github.com/ansible-community/ansible-bender/pull/173
* rpmdeplint - https://github.com/default-to-open/rpmdeplint/pull/1

## In review(copr):
* sen - https://github.com/TomasTomecek/sen/pull/150
* conu - https://github.com/user-cont/conu/pull/371

## Blocked:
### package not found
* Dockerfile-parse
* pretty-git-prompt
* cockpit-container

### Source in pagure?
* standard-test-roles

### Failures while srpm build
* cockpit
```
'Failed to parse SPEC file: [''warning: line 371: Possible unexpanded
macro in: Provides: bundled(js-jquery) = %{npm-version:jquery}'', ''error: line
371: Invalid version (epoch must be unsigned integer): %{npm-version:jquery}:
Provides: bundled(js-jquery) = %{npm-version:jquery}'']'
```
* pykickstart 
```
'Failed to parse SPEC file: [''error: Too many levels of recursion in
macro expansion. It is likely caused by recursive macro declaration.'', ''warning:
line 13: Possible unexpanded macro in: Version:   %VERSION%'', ''error: Too many
levels of recursion in macro expansion. It is likely caused by recursive macro
declaration.'', ''error: line 18: Source0:   https://github.com/pykickstart/%{name}/releases/download/r%{version}/%{name}-%{version}.tar.gz'']
```

## Needs action for spec generate:
* cockpit-composer
* cockpit-podman
* rpminspect
* ksh
* anaconda
* cockpit-ostree
