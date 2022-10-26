# Automatic Configuration Updates

Every now end then, a need to do a backward-incompatible change in `packit.yaml` arises (e.g. renaming a field in the config to a more precise name).
Currently, we have no convenient way of telling if all users have migrated their configs to the new format (so that the previous one can be removed) which slows down the process of deprecation. Moreover, in a lot of cases, we may be able to do the transformation for the user on our end.

## Possible high-level approaches

There seem to be 2 possible approaches how such updates could work on the top-level (for example the pre-commit bot does both of these):

1. When a user opens a pull request and we detect that the config in the PR can be transformed, we can push a new commit to the pull request.
2. We could periodically (or make this an action that can be triggered manually, e.g. a script that we run on the side) go over all the currently used configs and search for possible transformations and proactively make a PR to the respective repositories.

A disadvantage of 1) is that it requires user action (in the form of a PR).
If a project that has Packit enabled doesn't have any PR for a few months, during which we change the config and remove support for the old format, things like triggering `propose-downstream` won't work because the config will be invalid (because there was no PR where we could update it) and unparsable.
With this in mind, I consider 2) to be a must-have, while 1) to be a nice-to-have.

On the other hand, 1) has the advantage that it can fix the config of the user before it is merged to main if they try to use a deprecated feature, which 2) can't really handle (the config would be merged and then we would create a PR with the correction, so a correct config will end up on the main branch in the end).

## Implementation approach

Regardless of which of the following approaches ends up being used, the process of updating the config will always be the following:

1. Get the config, determine if transformations need to be done
2. Pull the repository
3. Make transformations to the config
4. Create a pull request (or add a commit to a PR) with the transformations

Let's take a closer look at the more "problematic" parts of this pipeline.

### Getting the config

There seem to be three main approaches to getting the config:

1. In case we do the modifications by adding commits to PRs, the config should come from the PR.
2. Get the list of projects by querying `/api/projects` and then find configs in them.
3. Add a new database table mapping project to its config content on main.

Let's focus on comparing 2) and 3) since those are relevant to the periodic updates.
Getting the list of projects with Packit enabled is straight-forward. However, we would have to do quite a lot of queries to Github to get all the configs (we could even run into Github's request quota).
Moreover, with this approach, we can't store any additional information about the config, which could perhaps be useful.

On the other hand, 3) would spread the requests to Github to get the current config across time. We would basically have to create an implicit action that triggers on merge to main/master and fetches the current config to the database. Hence, we wouldn't be making a lot of requests to Github at the same time, but rather over time.
This approach also facilitates storing additional data about the configs, for example which transformations have already been applied (see the following section).
Such additional information could allow us to detect that there are no transformations to do without even checking the config (resulting in faster overall updates).
The main downside of storing the configuration in the database are the space requirements.
However, this should hopefully not be a problem, since the config is usually not that long (but it is still something to keep in mind).

This approach also better facilitates analyzing user configs (for example when we want to know if a feature is used or if we can remove it) because we wouldn't have to make lots of requests to Github, just working with our database would suffice.

### Making transformations

The process of making configuration transformations looks to be analogous to making database migrations so that's where we should take some inspiration.

If a code change modifies the config in a backward-incompatible way (e.g. adds a new name for a field and deprecates the old one), the author of the code should also provide a transformation which will update the configs (if it's possible to do it automatically).

Each transformation should take in the config text, do some simple operations, and return the updated config (or the same config if no changes are necessary).
This way, we can easily chain the transformations.
To avoid unnecessary update attempts, we could "version" the transformations and then only try to do those which haven't already been applied.
To support this, we need to somehow map configuration to the index/version of transformation that was last applied (which would probably require approach 3) from the previous section).

Before completely removing a feature, we should check if all configs have been updated which requires analyzing the configs. The fact that we automatically opened a PR does not mean that it was really merged.

### Creating a pull request

Creating a PR should be trivial, however, we currently don't have permissions to do so (Packit Github application only requests read permissions of code).
According to [Github docs](https://docs.github.com/en/developers/apps/managing-github-apps/editing-a-github-apps-permissions), we should be able to easily modify this with an explaining message to our users why we are doing this.
However, from the docs, I am not sure if they somehow have to confirm Packit's permissions again or if it will work out of the box after doing the modification.
