# Updates of source-git repos


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
- Users can help with the sync. (Tweak the change.)
- No force-push possible.


### What can differ when going back to the dist-git structure?

- Be able to create the same `RPM` file?
- Can spec-file differ? e.g. different patch names, comments
  - Does the result have to be readable?
  - Is it a problem to have really high number of technical patches without sense?


## Proposal 1

### New changes

- When changing the patches save the line index and patch name with the commit
  (saving itself will be described later).
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
  - ➖ is not connected with the commit
- git note (see [Git Notes research](../git_notes) for more info):
  - ➕ attached to the git commit
  - ➕ can be changed, but not so easily as a regular file
  - ➖ not pulled automatically
- git-message
  - We can have strict format of the git-message (e.g. yaml).
  - ➕ attached to the git commit
  - ➕ pulled automatically
  - ➖ if we need to extend the info, we can loose readability
  - ➖/⁉ cannot be edited when pushed
- other file
  - ➕ editable by users
  - ➕ can be seen/reviewed
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
- Regenerate the source-git from scratch and use
  [ours](https://git-scm.com/docs/merge-strategieshttps://git-scm.com/docs/merge-strategies)
  merging strategy to merge the new version on top of the old version ignoring its content.
  - Alternatively, we can `revert` all commits and apply the new ones to have linear history.
    - All those newly-created commits can be squashed together to have only one new commit.
    - Will the revert of this work?
- We need to make sure that we go by the correct branch when reverting the content to the dist-git style.
  - Saving metadata (like above) can help us with that.

### Conclusion of proposal 2

- ➖ Git tree is unreadable.
- ➕ Source-git generation can be improved on the flow.
  (We can do any rapid change without being scared of the future.)
- ➕ Easy to implement.
- ⁉ Will reverting work? Can we go back in the right branch?
- ⁉ Conditional patching can be solved in the generation script.
  - We can theoretically generate multiple variants and let the user pick the correct one.
