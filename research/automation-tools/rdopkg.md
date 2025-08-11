---
title: RDOPKG
authors: flachman
---

- `rdopkg` is an RPM packaging automation tool.
- [ :computer: github.com/softwarefactory-project/rdopkgo](https://github.com/softwarefactory-project/rdopkg), [ :scroll: documentation](https://github.com/softwarefactory-project/rdopkg/blob/master/doc/rdopkg.1.adoc)
- ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rdopkg.svg), [![PyPI](https://img.shields.io/pypi/v/rdopkg.svg)](https://pypi.org/project/rdopkg/), [ :package: fedora packages](https://src.fedoraproject.org/rpms/rdopkg)

## :heavy_plus_sign:

- cloning package distgit and setting up remotes
- introducing patches
- rebases to new versions
- sending changes for review
- modifying .spec file: bumping versions, managing patches, writing changelog, producing meaningful commit messages, …
- persistence (`rdopkg --continue`) -- The state is stored in a file named `.rdopkg.json` in the current directory.

## :heavy_minus_sign:

- loosely coupled to RDO ecosystem -- need the following repositories:
  - upstream git
  - RDO distgit
  - patched git repo
  - metadata repo

## Patching branches

- patches ~ git commits
- same or different repository, for each distgit `$BRANCH`, there is a `$BRANCH-patches`
- `rdopkg` can rebase patches branch on new version.
- patch files generated automatically
- spec file changed automatically
- automatically dropping patches already included patches in the upstream

## Actions

- [fix](https://github.com/softwarefactory-project/rdopkg/blob/master/doc/rdopkg.1.adoc#action-fix) -- Apply changes to the `.spec` file.
  1. Bump Release, prepare a new `%changelog` entry header.
  2. Drop to shell, let user edit the `.spec` file.
  3. After running `rdopkg`, ensure description was added to `%changelog` and commit changes in a new commit.

- [patch](https://github.com/softwarefactory-project/rdopkg/blob/master/doc/rdopkg.1.adoc#action-patch) -- Introduce new patches to the package.
  1. Unless -l/--local-patches was used, reset the local patches branch to the remote patches branch.
  2. Update patch files from local patches branch using git format-patch.
  3. Update .spec file with correct patch files references.
  4. Unless -B/--no-bump was used, update .spec file: bump Release, create new %changelog entry with new patches' titles depending on -C/--changelog option.
  5. If a %global commit asdf1234 macro declaration is present, rewrite it with the current sha1 of the patches branch. (This makes the sha1 value available during your package’s build process. You can use this to build your program so that "mycoolprogram --version" could display the sha1 to users.)
  6. Create new commit (or amend previous one with -a/--amend) with the changes using %changelog to generate commit message if available.
  7. Display the diff.

- [new-version](https://github.com/softwarefactory-project/rdopkg/blob/master/doc/rdopkg.1.adoc#action-new-version) -- Update package to new upstream version.
  1. Show changes between the previous version and the current one, especially modifications to requirements.txt.
  2. Reset the local patches branch to the remote patches branch
  3. Rebase the local patches branch on \$NEW_VERSION tag.
  4. Update .spec file: set Version, Release and patches_base to appropriate values and create a new %changelog entry.
  5. Download source tarball.
  6. Run fedpkg new-sources (rhpkg new-sources).
  7. Update patches from the local patches branch.
  8. Display the diff.

- `-N`/`--new-sources` or `-n`/`--no-new-sources`

---

## Other sources

- [RDO OpenStack Packaging](https://www.rdoproject.org/documentation/intro-packaging/)
- [Let rdopkg manage your RPM package](https://blogs.rdoproject.org/2017/03/let-rdopkg-manage-your-RPM-package/)
