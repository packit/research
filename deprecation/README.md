# Deprecation policy

- `Deprecated` PyPI package is used for deprecation
- annotate deprecated functions with `@depracted` decorator, optionally with message
- functions will be removed in the 5th release after the release in which they were
  deprecated
- template for warning: `since {version}, will be removed in {version}: {alternative/message}`

## Choice of library

Looked into the options suggested by @lachmanfrantisek which were:

- `Deprecated`

  - seems as a good choice, offers decorator that has optional parameters such as version or custom message
  - live GitHub repo
  - fast release cycle
  - has only enhancements in issues
  - [docs](https://deprecated.readthedocs.io/en/latest/?badge=latest)
  - `@deprecated(reason='', version='', action='always', category=<class 'DeprecationWarning'>)`
    from docs, all properties are optional, you can add reason (usually alternative) or version in which it was deprecated

- `Python-Deprecated`

  - dead version of `Deprecated`, which is probably kept in PyPI just for backward-compatibility

- `deprecationlib`

  - seems like hobby project, only one information in decorator (alternative function name)

- `Dandelyon`

  - looks like nice project
  - offers multiple decorators
  - doesn't seem to be very active

- `deprecate`

  - dead project

- `deprecation`

  - not very active
  - multiple issues

- `libdeprecation`

  - dead version of `deprecation`

- `warnings` (built-in module)
  - seems like a lot of copy pasting of the same code, or manual implementation of `@deprecated`
