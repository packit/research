---
title: Updates of source-git repos (archived)
authors: flachman
---

This research is outdated and replaced by [research `packit source-git update-source-git`](/research/source-git/update).

## Problem

- We need to convert new dist-git commits to the existing source-git repository.
- The changes need to be reversible.
  - => We need to get back to the dist-git structure from the source-git.
- Possible changes:
  - changes in the packaging files (not in spec-file, not in patch files; e.g. config-files)
  - general changes in the spec-file (e.g. new release, new dependency, fixing a packaging problem)
  - change in patches:
    - patch added
    - patch edited
    - patch removed
- Patches can be applied conditionally (or even manually).
- Users can help with the sync. (Review and tweak the change.)
  - Note from the demo meeting.
    For some users, it is not a problem to be able to make source-git generating locally.
    They can review (and potentially) improve/correct the result.
  - Do we want to allow it? How can we do it to no break the workflow?
- No force-push possible.

### What can differ when going back to the dist-git structure?

- Be able to create the "same" `RPM` file? What is "same"?
- Can spec-file differ? e.g. different patch names, comments
  - Does the result have to be readable?
  - Is it a problem to have really high number of technical patches without sense?

## Proposal 1

### New changes

- When changing the patches save the line index and patch name with the commit
  (saving itself is described bellow).
- Create a new source-git commit:
  - patch added:
    - convert patch to source changes
    - save `{"patch": "name.patch", index=42}` with the commit
    - comment out the line with the patch
  - patch removed:
    - invert the patch and convert to the changes
    - save `{"patch": "name.patch", index=-42}` with the commit
    - remove the line with the patch
  - patch edited:
    - convert patch diff to source changes
      - diff of patches / revert+new change
    - save `{"patch": "name.patch", index=42}` with the commit
    - line with patch should be already commented

### Reverse

- When going back from commit to patch:
  - In case of commit without metadata:
    - Generate a patch file and add it to the spec-file.
  - In case of `index >= 0` in the metadata:
    - Check the existence of the `name.patch`:
      - If not present:
        - Uncomment the `index` line in the spec-file.
        - Generate `name.patch` from the commit.
      - If present:
        - Generate a new path from the commit and merge it into `name.patch`.
  - In case of `index == -42`:
    - Remove the `name.patch`.
    - Remove the line `42` in the spec-file.

### Saving metadata

We have various way, how to save metadata for regeneration:

- Enhance packit config file:
  - ➕ editable by users
  - ➕ can be seen/reviewed
  - ➕ preserved between git commits
  - ➖ is not connected with the commit (the mapping can be added)
- git note (see [Git Notes research](../git_notes) for more info):
  - ➕ attached to the git commit
  - ➕ can be changed, but not so easily as a regular file
  - ➖ not preserved between git commits (easier usage if we use it together with second proposal)
  - ➖ not pulled automatically
- git-message
  - We can have strict format of the git-message (e.g. yaml).
  - ➕ attached to the git commit
  - ➕ pulled automatically
  - ➖ if we need to extend the info, we can loose readability
  - ➖ not preserved between git commits (easier usage if we use it together with second proposal)
  - ⁉ cannot be edited when pushed
  - Will be read by users => users can not like it.
  - If we want to allow users to write it as well,
    we need to have some wrapper on top of git to ease that.
- other file
  - ➕ editable by users
  - ➕ can be seen/reviewed
  - ➕ preserved between git commits
  - ➖ is not connected with the commit
  - ➖ another file

### Conclusion of proposal 1

- We need to add metadata to the source-git commits.
  - Can be used for other information.
  - Depending on the saving mechanism (above) it can reduce/break the usual git usage.
- ➕ The git history is clear.
- ➖ A lot of work needs to be done.
  - Multiple scenarios; lot of corner cases.
- ➖ It will be hard to correct/improve the workflow.
- ➕ Reverted dist-git still preserves the conditions, naming and location of the patches.
- ➖ Generated source-git will contain all the patches.
  - Various improvements and strategies possible and doable later
    (e.g. avoid both of if-else branches, expand macros before getting of the patches).

## Proposal 2

- Easy solution that mimics the history overwriting without force push.
- There are multiple ways, how to do this:

  - (I) Regenerate the source-git from scratch and use
    [ours](https://git-scm.com/docs/merge-strategieshttps://git-scm.com/docs/merge-strategies)
    merging strategy to merge the new version on top of the old version ignoring its content.
    (Packit does not work now with upstream-ref outside of the linear history.)

    ![git-merge-ours](img/git-merge-ours.jpg)
    ![git-merge-ours-with-comments](img/git-merge-ours-with-comments.jpg)
    ![git-merge-ours-new](img/git-merge-ours-new.jpg)

  - (II) Use force checkout the content instead of merge to have regular commit instead of the head one.

    ![git-force-checkout](img/git-force-checkout.jpg)

    ```bash
    # generate new source-git to `rpm-4.14.2-36.el8` branch starting on master
    git checkout c8s
    git checkout -f rpm-4.14.2-36.el8 -- .
    # use the `sg-start-rpm-4.14.2-25.el8` as upstream-ref in config
    # (use the old one => revert that change)
    git commit -m "Update from distgit"
    ```

    ```bash
    * d3ec53a - Update from distgit (c8s)
    * 9eba783 - Apply Patch1002: rpm-4.14.2-unversioned-python.patch (rpm-4.14.2-25.el8)
    * 9609ba3 - Compile with Platform-Python binary where relevant
    :
    * 5513f1d - Apply Patch1: rpm-4.11.x-siteconfig.patch
    * ce19f5d - Downstream spec with commented patches (tag: sg-start-rpm-4.14.2-25.el8)
    * 7c6a6b1 - .packit.yaml
    * 49dd86b - Unpack archive
    * fbcb954 - init (master)
    ```

    ```
    commit d3ec53a11e62cb01252ddd166864e1b9ed6a84e1 (HEAD -> c8s)
    Author: Frantisek Lachman <flachman@redhat.com>
    Date:   Thu Jun 11 09:35:01 2020 +0200

        Update from distgit

        Signed-off-by: Frantisek Lachman <flachman@redhat.com>

     SPECS/rpm.spec                   |  69 +++++++++-
     build/files.c                    |  31 ++++-
     build/pack.c                     |  34 ++++-
     :
     tools/debugedit.c                | 584 +++++++++++++++++++++++++++++++++++++++++++++++++++++-------------------------
     26 files changed, 628 insertions(+), 270 deletions(-)
    ```

    ```bash
    $ packit srpm
    Input directory is an upstream repository.
    100%[=============================>]     3.96M  eta 00:00:00
    44 patches added to '/home/flachman/Projects/git.centos.org/src/rpm/SPECS/rpm.spec'.
    SRPM: /home/flachman/Projects/git.centos.org/src/rpm/rpm-4.14.2-37.gd3ec53a1.fc32.src.rpm
    ```

  - (III) Another alternative is to revert to the initial commit
    (we should start with some neutral state) and rerun the generation script.
    This will have upstream tag in the right place and will have a linear history.

    ![git-revert-to-init-1](img/git-revert-to-init-1.jpg)
    ![git-revert-to-init-2](img/git-revert-to-init-2.jpg)

    ```bash
    * 46b055b - Apply Patch1002: rpm-4.14.2-unversioned-python.patch (c8s)
    * f20e0c9 - Compile with Platform-Python binary where relevant
    * 5f7b687 - Apply Patch1000: disable-python-extra.patch
    :
    * 41f0dd8 - Apply Patch1: rpm-4.11.x-siteconfig.patch
    * 0488837 - Downstream spec with commented patches (tag: sg-start-rpm-4.14.2-36.el8)
    * 3cf64a9 - .packit.yaml
    * ef4b7f6 - Unpack archive
    * 3bbc954 - revert-to-init
    * 9eba783 - Apply Patch1002: rpm-4.14.2-unversioned-python.patch
    * 9609ba3 - Compile with Platform-Python binary where relevant
    * a43a233 - Apply Patch1000: disable-python-extra.patch
    :
    * 5513f1d - Apply Patch1: rpm-4.11.x-siteconfig.patch
    * ce19f5d - Downstream spec with commented patches (tag: sg-start-rpm-4.14.2-25.el8)
    * 7c6a6b1 - .packit.yaml
    * 49dd86b - Unpack archive
    * fbcb954 - init (master)
    ```

    ```bash
    $ git diff 9eba783 46b055b --stat
    .packit.yaml                                                                                                                               |      2 +-
     SPECS/0001-Unpack-archive.patch                                                                                                            | 696860 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
     SPECS/{0001-Apply-Patch1-rpm-4.11.x-siteconfig.patch.patch => 0002-Apply-Patch1-rpm-4.11.x-siteconfig.patch.patch}                         |      6 +-
     SPECS/{0002-Apply-Patch2-rpm-4.13.0-fedora-specspo.patch.patch => 0003-Apply-Patch2-rpm-4.13.0-fedora-specspo.patch.patch}                 |      6 +-
     SPECS/{0003-Apply-Patch3-rpm-4.9.90-no-man-dirs.patch.patch => 0004-Apply-Patch3-rpm-4.9.90-no-man-dirs.patch.patch}                       |      6 +-
     :
     SPECS/0044-Use-newline-as-a-delimiter-to-avoid-xargs-messing-up.patch                                                                      |     26 -
     SPECS/0045-Make-check-buildroot-check-the-build-files-in-parall.patch                                                                      |     31 -
     :
     rpm-4.14.2-38.g9b8c91d8.fc32.src.rpm => SPECS/rpm-4.14.2.tar.bz2                                                                           |    Bin 4251502 -> 4151934 bytes
     SPECS/rpm-4.14.3.tar.bz2                                                                                                                   |    Bin 0 -> 5059526 bytes
     SPECS/rpm.spec                                                                                                                             |     69 +-
     build/files.c                                                                                                                              |     31 +-
     :                                                                                                                         |    584 +-
    ```

    ```bash
    $ packit srpm
    Input directory is an upstream repository.
    44 patches added to '/home/flachman/Projects/git.centos.org/src/rpm/SPECS/rpm.spec'.
    SRPM: /home/flachman/Projects/git.centos.org/src/rpm/rpm-4.14.2-37.gd3ec53a1.fc32.src.rpm
    ```

- We need to make sure that we go by the correct branch when reverting the content to the dist-git style.
  - Saving metadata (like above) can help us with that.

### Conclusion of proposal 2

- Final git tree:
  - version (I)
    - ➖ Packit does not work with `upstream-ref` in merged branch
    - ➕ We can still see the history of all generated source-gits.
    - ➖ A lot of branches around.
  - version (II)
    - ➖ The old source-git history in the git history can be outdated.
      (Still contains the commits from the first run.)
    - ➖ We loose the history about creation of new source-git.
    - ➕ Git history is clear. Just one new commit.
      - Effectivelly, same content as the manual approach.
  - version (III)
    - ➕ contains the last source-git generation history
    - ➖ lots of unnecessary commits from the last runs, that are reverted each time
- ➕ Source-git generation can be improved on the flow.
  (We can do any rapid change without being scared of the future.)
- ➕ Easy to implement.
- ⁉ We still need to save metadata to fix problems like conditional patching.
- ⁉ Conditional patching can be solved in the generation script.
  - We can theoretically generate multiple variants and let the user pick the correct one.
