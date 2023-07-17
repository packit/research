---
title: Updating source-git
authors:
  - csomh
  - ttomecek
---

# `packit source-git update-source-git`

This research covers a command which synchronizes file changes from a dist-git
repo back to a source-git repo.

Areas to cover:

- spec file synchronization

- packaging sources synchronization

- code synchronization

Let's break these down.

## Spec file sync

Packit should copy the file from dist-git back to source-git. But before doing
that, we should capture the `%version` spec file tag and check if it differs
from the source-git spec. If it does, it means that we're dealing with a rebase
which is not supported and packit should inform the user about this fact. See
"Version changed" section below.

If the `%release` tag has changed, packit should inform the user about the
different release numbers. This is not an issue and is actually expected to
happen during the proven-packager workflow when the release number is increased
by 1 for sake of a rebuild.

## Packaging sources synchronization

These cover additional files in dist-git (except for patches and the "sources"
file). Packit should detect a removal of a file and also remove it in
source-git's `.distro` folder. Otherwise it's the same drill as with the spec
file - copy the files.

## Code synchronization

There are 2 use cases in this bucket:

1. Patches were changed, removed or added
2. The package was rebased to a new version

At first, we should be able to detect that such a thing has happened. There are
multiple ways how to do that:

- inspect commits and check what files have changed: if sources file or patch files
  changed, we can easily tell that source code has changed.
- parse spec file and compare `%version` between dist-git and source-git

Packit should not support any of these 2 cases: users have to still perform
work in their source-git repos first and not in dist-git.

One problem with detecting changes is that we do not track which source-git
commit matches a dist-git commit and vice versa. We should start with requiring
a git-range which should be synchronized and over time figure out if this can
be automated. Alternatively we can start putting metadata into our dist-git
commits to tell which source-git commit they are matching.

### Patches were changed

1. A patch was removed
2. A patch content changed
3. A patch was added

### Package was rebased

The package was rebased to a different version which likely resulted into
several patches being dropped and a change in git-history in source-git.

## CLI proposal

```
Usage: packit source-git update-source-git [OPTIONS] DIST_GIT SOURCE_GIT REVISION_RANGE

  Update a source-git repository with selected checkout of a spec file and
  additional packaging files from a dist-git repository.

  Revision range represents dist-git history which should be synchronized. Use
  `HEAD` if you want to synchronize the current checkout. For more info how to
  specify the revision range, see git-log(1).

  If patches or the sources file changed, the command exits with return code 2.
  Such changes are not supported by this command - code changes should always
  happen in the source-git repo first.

  This command, by default, performs only local operations and uses the
  content of the source-git and dist-git repository as it is: does not
  checkout branches or fetches remotes.

  After the synchronization is done, packit will inform about the changes it
  has performed and about differences between the two repositories prior to the
  synchronization process.

  Commit messages are preserved by default.

  Examples:

  Take the current checkout (HEAD) of systemd dist-git repo and copy spec file
  and other packaging files into the source-git repo at src/systemd

    $ packit source-git update-source-git rpms/systemd src/systemd HEAD

  Synchronize changes from the last three dist-git commits

    $ packit source-git update-source-git rpms/systemd src/systemd HEAD~3..

Options:
  -h, --help           Show this message and exit.
```
