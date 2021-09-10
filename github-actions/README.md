# GitHub Actions

## Benefits and options for Packit and users of Packit

### Customization as a whole

In case of providing Packit API via GitHub Actions it allows to run pipeline (SRPM → Copr →
Testing Farm) after:

- running some initial CI checks (saves resources on our side)
- preparing archives (eliminates need for retries and failed jobs on our side, if they are blocked
  by some external action)

### SRPM builds

- Allows user to **easily** customize the dependencies, i.e. does not require changes to be made to
  the Sandcastle image.
- Provides access to created SRPMs without dependency on Copr or Packit Service.

## Disadvantages and caveats

### SRPM builds

- If we were to trigger Copr builds with SRPM created in GitHub Action we introduce blocking action of
  acquiring the SRPM from GitHub.
- No cache is present, which also introduces:
  - slower build time
  - potential time out, since Actions are time limited (iirc 24 hrs per action)

### Security concerns

In case of utilizing API via GitHub Actions there is a risk of modifying actions that could result
in leaking of the secrets. GitHub mitigates this by censoring the output of GitHub Actions, but with
our use-case it would be still possible to (indirectly) modify scripts that are run and leak the
secrets.

Possible options how to prevent this are:

- inject secrets after running all customizable actions
- do not run the action if user has no write-access (enforces check by the maintainer)
  - differentiating «maintainer approved»?
  - how to decide if changes can be evaluated or not? (i.e. user is trusted to modify the files)
    - list of files that cannot be modified externally? However it might be required to get those
      from the default branch, since branch where changes are merged may be compromised.

### Versioning

In case we do not provide specialized images on which Packit can be run, we can run into issues with
different versions of Packit being used (RPM vs PyPI vs images).

## How can we use it

### SRPM build

_TODO_

### Local RPM build

_TODO_

### Mock RPM build

_TODO_

### Copr RPM build

_TODO_

### Testing Farm

_TODO_

#### Running tests in GitHub Action

_TODO_

#### Testing farm via API from GitHub Action

_TODO_

### Rough estimation of time required

_TODO_

## Sharing the work done with GitLab (and potentially Pagure)

_TODO_
