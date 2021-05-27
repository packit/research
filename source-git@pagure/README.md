# Pagure as a source-git platform

It seems that the Fedora community wants to pursue pagure.io as the git forge platform.
Let's have a look at what it would take to use it to host Fedora source-git repos in there.

## Requirements/functionality

From [Franta's research](https://github.com/packit/research/tree/main/split-the-stream#what-does-the-source-git-workflow-mean):

(sg == source-git, dg == dist-git)

### Must:

- New sg PR is transformed into a new dg PR
  - New PR event - fedora-messaging: [pull-request.new](https://fedora-fedmsg.readthedocs.io/en/latest/topics.html#pagure-pull-request-new)
  - Create new PR - “Create pull-request” in [API](https://pagure.io/api/0/#pull_requests-tab)
- dg PR CI results are mirrored back to sg PR
  - Get CI results - fedora-messaging: [pr.flag.added](https://fedora-fedmsg.readthedocs.io/en/latest/topics.html#pagure-pull-request-flag-added) / [pr.flag.updated](https://fedora-fedmsg.readthedocs.io/en/latest/topics.html#pagure-pull-request-flag-updated)
  - Set CI results - “Flag a pull-request” in [API](https://pagure.io/api/0/#pull_requests-tab)
- If the dg is updated, update the sg repository by opening a PR
  - Dg updated - fedora-messaging: [git.receive](https://fedora-fedmsg.readthedocs.io/en/latest/topics.html#pagure-git-receive)
  - Open new PR - “Create pull-request” in [API](https://pagure.io/api/0/#pull_requests-tab)

### Should:

- If the sg PR is updated/closed, update/close the dg PR
  - PR updated/closed - fedora-messaging: [pr.updated](https://fedora-fedmsg.readthedocs.io/en/latest/topics.html#pagure-pull-request-updated) / [pr.rebased](https://fedora-fedmsg.readthedocs.io/en/latest/topics.html#pagure-pull-request-rebased) / [pr.closed](https://fedora-fedmsg.readthedocs.io/en/latest/topics.html#pagure-pull-request-closed)
  - Update PR - git force-push to existing branch
  - Close PR - “Close a pull-request” in [API](https://pagure.io/api/0/#pull_requests-tab)

### Could:

- User is able to re-trigger the dg CI from the sg PR
  - If the user comments `/citest` on the sg PR, retrigger dg CI by adding a `[citest]` comment via [API](https://pagure.io/api/0/#pull_requests-tab).
- User is able to re-create the dg PR from the sg PR
  - If the user comments `/update-dist-git` in the sg PR, update and force-push the content of the dg PR.

## Notes

There are 2 ways of getting notifications about events (PR opened/updated etc.) from pagure:

- Webhooks - to [verify messages](https://docs.pagure.org/pagure/usage/using_webhooks.html), receiver (our service) needs to know a private webhook key, which is set in repositories and is unique for each repo
- Fedora-messaging - no verification mechanism, but we “know” the `pagure.*` topic is from pagure

Pagure has [CI integration](https://docs.pagure.org/pagure/usage/pagure_ci.html) but seems to support Jenkins only.

In `Project Settings` -> `Hooks` one can set Mirroring to mirror a repo hosted on pagure to another location.
