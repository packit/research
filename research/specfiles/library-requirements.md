---
title: Requirements for the specfile library
authors: flachman
---

## Manipulation

- We create a Python object by specifying a path of the spec-file and (optionally) path to spec-file sources
  (the directory with the spec-file).
- (optional) After a change, we can reload the content (can be done by recreating of the object).
- After the manipulation, the content is synced to the file or, we have a way to do this explicitly.
- Be able to copy a section of spec-file to another object.
- When reading the values, we want to be able to have both version with macros expanded
  and raw without expansion.
- When changing the spec-file, we want to operate on the raw spec-file.
  - All changes results in a minimal and local diff.

## Version and release

- The version and release fields can be get.
- We can set the new version. If release is not specified, reset the release number to 1.

## Changelog

- We can get the content of the changelog.
- We can add a new changelog entry:
  - By providing only the changelog text.
  - Optionally, field like `name` or `email` can be specified.
    (Defaults of bumbspec are used by default.)

## Sources

- We can get the sources and patches.
- We can download the sources from a lookaside cache.
- We can download remote sources (sources in form of URL).
- We can change the value of a source.
- We can get archive name for source.

## Comments

- For patches and other fields, we want to add a comment without a need to manipulate with the file directly.
  - What about having a get/set `comment` value for various spec-file attributes for comment lines right above the item without any non-comment line?

    ```
    # this is
    # the comment
    # for the first source
    Source1: source1.tar

    # this is not a comment for the second source

    Source2: source2.tar
    ```

## Patches

- We can get the patches.
  - Including the comment above (see the section above).
- We can add a new patch:
  - Automatically pick the right number.
  - Check if the patch isn't already present.
  - If there already are patches, then the patch is added after them.
  - If there are no existing patches, the patch is added after Source definitions
  - Be able to set a comment used above the patch line (see the section above).
- Concept of applied patches. (Probably source-git specific.)
  - Behave like a commented patch.
  - We are able to list the applied patches.
  - We can apply the patches = comment the patch.
- We can remove all the patches.

# Other content

- We can get and replace the method used in `prep` section (e.g. `autosetup`, `setup`, `autopatch`,...).
- Get URL tag.

# Workflows (can be implemented elsewhere but would be nice)

- Bumbspec: change version and add a new changelog entry.
- Be able to copy content of the whole spec-file to another object and be able to ignore a section during that (e.g. whole content but the changelog).

## Functionality used from rebase-helper but not connected to the spec-files

- Get the upstream version using [Upstream Release Monitoring](https://fedoraproject.org/wiki/Upstream_release_monitoring?rd=Upstream_Release_Monitoring).
