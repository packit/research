# Verifying the sync status of source-git and dist-git repos

A source-git repo is in sync with the corresponding dist-git repo, if an attempt
to sync the former to the later (by running `packit source-git update-dist-git`)
does not produce any change in the dist-git repo.

Being out-of-sync can mean:

- There are commits in source-git which were not yet transferred to dist-git.
- There are commits in dist-git, which were not created as an update from
  source-git, and need to be synced back to it.
- Both of the above (source-git and dist-git history has diverged).

From an operational point of view, dist-git changes will need to be synced
back to source-git, before accepting content to be transformed from source-git
to dist-git, in order to be able to preserve dist-git as the "blessed" place
to store the sources. In other words: all new changes to be synced from
source-git to dist-git should be based on a commit matching the current state
in dist-git.

In order to help with this, both update commands
(`packit source-git update-dist-git` and `packit source-git update-source-git`)
should refuse to update the destination repository if the head commit in the
destination repository doesn't have it's pair commit among the ancestors of
the current head commit in the source repository. Nevertheless, it should be
possible to override this with a `--force` flag, to allow developers to
override tooling or human errors and bring the repositories back in sync.

## CLI proposals

The naïve way to check if the two repositories are in sync is to run
`packit source-git update-dist-git`. But this goes over the entire process to
transform content from source-git to dist-git, which might not be practical
when looking just for the information whether the repos are in sync, and if
they are not, to tell the (range of) commits to be synced.

Note, that the list of commits (or rather the range of commits) to be synced is
relevant only when syncing from dist-git to source-git. Transformation in the
other direction always considers the commits since `upstream_ref`, so in this
case the range of outstanding commits would only serve as an information for the
user.

The CLI for the sync-check can be implemented as a new sub-command for
`packit source-git`:

```
    $ packit source-git status src/acl rpms/acl
```

The command would have the following outputs:

- Print the range of commits (as a Git-revision, i.e: `HEAD~<n>..`) in
  source-git which need to be synced to dist-git, if any.
- Print the range of commits (as a Git-revision, i.e: `HEAD~<n>..`) in
  dist-git which need to be synced to source-git, if any.
- Print a message that the repositories are in sync if that's the case.

## Marking the origin of synced content

In order to be able to tell whether a commit in the dist-git or source-git
history has originated from the corresponding sibling repository the _full
hash_ of the source commit should be recorded. This can be done with some
dedicated [Git-trailers], appended at the end of the commit messages.

Commits created by `packit source-git update-dist-git` in dist-git repositories
should have:

```
    From-source-git-commit: <head-commit-hash>
```

Commits created by `packit source-git update-source-git` in source-git
repositories, and the commit at the tip of the branch, created by
`packit source-git init` should have:

```
    From-dist-git-commit: <head-commit-hash>
```

## Identifying commits to sync

Search the commits of the current branch in each repository and look for the
last (latest) commit which has the Git-trailers above.

    $ git log -1 --grep='^From-source-git-commit: .\+$'
    $ git log -1 --grep='^From-dist-git-commit: .\+$'

Identify the pair-commits from the other repository.

Tell which pair is the latest. The commits to be synced are the ones newer
than the latest pair.

### Example

Given the following history:

```
Source-git                    Dist-git

   E *
     |
   D *                           * 4
     |                           |
   C * (From: 3)  <------------  * 3
     |                           |
   B * ------------>  (From: B)  * 2
     |                           |
   A * (From: 1)  <------------- * 1
```

Commit `C` in source-git and commit `2` in dist-git would be found as the ones
having the Git-trailers.

The commit pairs would be: `B-2` and `C-3`.

The newest pair is `C-3`, so `HEAD~2..` needs to be synced from source-git to
dist-git and `HEAD~1..` needs to be synced from dist-git to source-git. (In
other words: the history of source-git and dist-git has diverged.)

## Proposed tasks

1. Update `source-git` commands to mark the commit origin with Git-trailers
2. Modify `source-git update-*` commands to check the sync-status
3. Implement checking the sync-status

[git-trailers]: https://git-scm.com/docs/git-interpret-trailers
