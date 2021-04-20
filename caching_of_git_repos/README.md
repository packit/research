# How to cache git repositories with a reference repo

## The main idea

Using `git clone --reference /repo/with/cache https://some/repo/to/clone`.

What it does?

- When cloning a repo, you can specify a repo, that will be searched first for commits to download.
  (If the commit is found in the reference repo, reference is used instead of saving the data.
  If not found, commit is downloaded and data saved.)

  --reference[-if-able] <repository>
  If the reference repository is on the local machine, automatically setup .git/objects/info/alternates to obtain objects from the reference repository. Using an already existing repository as an alternate will require
  fewer objects to be copied from the repository being cloned, reducing network and local storage costs. When using the --reference-if-able, a non existing directory is skipped with a warning instead of aborting the clone.

- The state of the reference repo is not important.
  (We don't need to care about force-pushes, merging, local changes,...)
  What is fetched counts.
- We can fetch commits of multiple repositories in the reference repository.
  - Alternatively, we can use more cache repositories:
    `git clone --reference-if-able /cache/some-repo-to-clone https://some/repo/to/clone`

## Pros&Cons

- Cloning is much faster for repositories in the cache.
- Cloning is slower for repositories not present in the cache.
- Less memory is needed to clone repositories in the cache.
  (Which makes it possible to clone kernel for example.)
- More memory is needed to clone repositories not present in the cache.
  - e.g. 1000m needed to clone ogr using cache repo with kernel-ark and systemd (800m has not been enough)
- Less storage is needed for the cloned repo if it is in the cache.
  (Only the current state of the repo is saved, historical commits reference the cache repo.)

## Where to store this cache repository?

- The cache does not need to be writable for cloning.
  Only for creating/updating.
- Persistent volumes can be used.
- How much storage we can afford?
  - Storage is cheap, but git repositories can be really big after some time.
  - I haven't tested efficiency of the scenario with a lot of repositories in one cache repository.
- Data itself can be shared between stage/prod if we want. (Probably not wanted and hard to do in openshift.)

## How to create the cache repository?

- Manually on request. Mount the volume once with more memory and fetch the needed repository.
- Manually on sentry issue. As previous but gather the problematic repos in sentry.
- Start with kernel manually and add new ones on the go.

## What repositories we want there?

- Just kernel.
- A group of hardcoded/configured repositories.
- All repositories matching some condition (at least some commits, some size, ...)
- All repositories. (Add if not present.)

## When we want to use this mechanism?

- Everytime. It is possible, but it can be time/memory consuming to use it for new repositories.
- Only on the repos matching the origin. (Will not work for forks/renames.)
  We can cache the list to not need to read it multiple times.
- Use the `--reference-if-able` and have one repo for each project.
  (Similarly to the previous one, forks/renames will not work.)

## How to update the repositories?

Updating of some bigger repositories can require more memory we used to have for workers.

- Manually. (`git fetch --all`)
- As a cron job. (daily x hourly x weekly)
- As a celery task. (As a reaction on empty queue?)

## How can this be implemented?

Currently, cloning is done lazily in LocalProject.

1. In case of the very basic version, we can make packit agnostic to this
   by being able to configure additional arguments for clone commands:
   - [packit] Enhance the schema of the user config.
   - [packit] Use this value when cloning (LocalProject).
   - [deployment] Add persistent volume.
   - [deployment] Use `--reference /persistent/volume` in the service config.
2. Alternatively, we can have the cache directory configurable (optionally).
3. If we want more clever behaviour, we need to put the cloning logic to packit.
4. Or, we can forward some method for handling the cloning.
   (Defined in the service repo, run in the packit.)

## Is this relevant for the CLI users?

Can help to avoid long cloning during some commands:

- using temporary distgit repo (default)
- using URL instead of the local git repository as an input

To give it some value, we need to:

- add new repositories automatically
- provide a way to update the cache (automatically/manually)

It looks like it can be useful if the implementation can be shared,
but it does not make sense to spend a lot of time on CLI-only code.
