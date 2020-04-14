# External Testing

Let's talk about testing process against external resources. What does that
mean? Well, talking to GitHub API, COPR API, running `fedpkg`, cloning
repositories...


## Use cases

* Interact with an external API (such as GitHub, COPR, Pagure, FAS, k8s)
  * Authenticated vs. unauthenticated calls.
* Clone a git repository.
* Construct a git repository with a predefined structure by us.
* Run a command to perform an action.
  * Changes happening only locally.
  * RO access to a remote service.
  * R/W access to a remote service.
* Combination of multiple use cases into a single test case.


## How we test today

We have the use cases, let's see how we are solving them w/ requre (and other tools) today:
* The record/replay configuration is often set outside of tests so one needs to track down matching configuration for a test case.
* `upgrade_import_system().decorate(...)...` makes it hard to know why some of the entries are in the chain.
  * `what`, `where` and `who_name` are very confusing and am pretty sure that only Honza knows their true meaning.
* Some recorded responses are hard to pair with their respective code.
  * (Example: `X → file → tar → StoreFiles → tests...test_comment_in_spec → ... output: !!binary`)
* WIP [PR](https://github.com/packit-service/packit/pull/612) from Franta on moving more tests to use requre:
  * We need to have [switches](https://github.com/packit-service/packit/pull/612/files#diff-c2e2e7a23e6a4cefc8ba3ff9ec18c866R189) in code when a dependency changes its internals significantly to account for the call stack difference.
  * Fairly complex [testing setup](https://github.com/packit-service/packit/pull/612/files#diff-c2e2e7a23e6a4cefc8ba3ff9ec18c866).
  * [Tests themselves](https://github.com/packit-service/packit/pull/612/files#diff-db8ce5f26d68799608c6cab5aae59fdc) are short and concise.
  * requre is used to record these interactions:
    * HTTP communcation
    * `git push`
    * `git fetch`
    * `fedpkg clone`
    * storing files (which?)
* We still have 2 PRs opened to improve testing via requre in packit and p-s, for months at this point.
* Our integration tests use pytest features and flexmock heavily - the structure is too complex at this point.


## VCRpy vs. requre vs. betamax

| A feature | VCRpy | requre | betamax |
|-----------|-------|--------|---------|
| Record & replay for python requests | ✓ | ✓ | ✓ |
| Match on call stack | ✘ | ✓ | ✘ [5]|
| Match on URL & request type | ✓ | ✘ | ✓ |
| Hooks to all requests calls automagically | ✓ | ✓ | ✘ [6] |
| Calling the same URL twice works as expected | ✓ | ✘ | ? |
| Works with HTTPS | ✓ | ✓ | ? |
| Record & replay for arbitrary functions | ✘ | ✓ | ✘ |
| Filtering sensitive data out of recorded responses | ✓ [1] | ✓ [2] | ✓ [7] |
| Easy to use | ✓ [3] | ✘ [4] | ? |
| Actively maintained | ✘ | ✓ | ~ |

* [1] https://vcrpy.readthedocs.io/en/latest/advanced.html#filter-sensitive-data-from-the-request
* [2] https://requre.readthedocs.io/en/latest/usages/postprocessing.html
* [3] [You can use a decorator or a context manager](https://vcrpy.readthedocs.io/en/latest/usage.html)
* [4] [Tenths of lines of code](https://github.com/packit-service/packit/blob/master/tests_recording/__init__.py#L16) [which are very hard to understand](https://github.com/packit-service/packit/blob/master/tests_recording/testbase.py#L22)
* [5] Betamax has [pluggable matching mechanism](https://betamax.readthedocs.io/en/latest/matchers.html)
* [6] This is by design: https://github.com/betamaxpy/betamax/issues/125#issuecomment-267405773
* [7] https://betamax.readthedocs.io/en/latest/serializers.html

### Feelings

These are my personal (@TomasTomecek) comments and opinions:
* VCRpy's API and documentation is focused on the record & replay use case
  which makes it very pleasant to work with.
* requre's documentation and API is centered around implementation details
  which makes it very configurable, but unfortunately extremely hard to work
  with - even to the point that you need to understand internals.
* VCRpy in action:
  * [Basic usage](https://github.com/packit-service/packit/pull/785)
  * [Calling the same URL twice](https://github.com/packit-service/ogr/pull/373)
* The fact that requre is matching replay via call stack makes it less flexible
  and requires data regeneration more often than VCRpy.
* In my opinion: VCRpy masters its job very well.


## So, what's next?

Hunor asked me to do an in-depth analysis for the possible solutions. We need
a team discussion to pick one.


### Solution 1: Keep using requre and improve it

We can keep using requre as we are now. But given that VCRpy has
* very neat user experience
* and matches requests based on their data and not the call stack,

it is very compelling to have VCRpy's experience. This means that if we stick
to using requre, we need to improve it to match VCRpy's UX.

21+ story points probably and weeks of polishing it (2 sprints at least)


### Solution 2: Switch to VCRpy

Alternatively, we can switch to VCR. There are multiple sub-options.


#### a) Get requre's features in there

Since VCRpy has "dead upstream" we would either ended up
* maintaining the project
* or forking it

Definitely more work than implementing things in requre itself.

21++ story points (2-3 sprints)


#### b) VCRpy + flexmock + pytest fixtures

This implies ditching requre completely. We'd need to:
* rewrite existing tests to use VCR instead of requre (easy)
* regenerate or transform data (should be easy)
* use flexmock (or something else) for git, fedpkg...
* most importantly: prepare the structure well so it's not messy

This should be achievable in 2 sprints.

Technical arguments end here and personal preference would follow.


### Not a solution 3: VCRpy + requre

They don't play well together. This solution doesn't make any sense.


### Not a solution 4: Switch to betamax

This is a no-go: we would need to "rewrite" most of our tests and patch all the
client libraries we use. No.

