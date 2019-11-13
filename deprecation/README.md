# Deprecation policy

* `Deprecated` PyPI package is used for deprecation
* annotate deprecated functions with `@depracted` decorator, optionally with message
* functions will be removed after 6 months from the release in which they were marked as deprecated

## Choice of library

Looked into the options suggested by @lachmanfrantisek which were:

* `Deprecated`
  * seems as a good choice, offers decorator that has optional parameters such as version or custom message

* `Python-Deprecated`
  * deprecated `Deprecated`, which is probably kept in PyPI just for backward-compatibility

* `warnings` (built-in module)
  * seems like a lot of copy pasting of the same code, or manual implementation of `@deprecated`
