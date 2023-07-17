---
title: Configuration versioning
authors: lbarczio
---

Example use cases we would like to solve with this:

- Example 1: Image builder job - it will probably evolve over time depending on the requirements
- [Example 2](https://github.com/packit/packit.dev/issues/443): Changing interpretation of job overrides from replacing the values to merging

## Existing support

- no support from Marshmallow, [see](https://github.com/marshmallow-code/marshmallow/issues/1107)
- in general, I have not found any existing support to do this
- some tips from the issue above:
  - utilising `render_module` (from [this class](https://marshmallow.readthedocs.io/en/3.0/api_reference.html#marshmallow.Schema.Meta)) - a class that defines loads and dumps, which defaults to json,
    could be a good place to intercept the raw data on a per-schema basis
  - migrating the raw data before deserializing to avoid maintaining a schema history

## Versioning jobs aside from the whole config

- this would be mostly beneficial for versioning only one job type (e.g. vm_image_build)
- since all the job-related fields in the job config are grouped in a class together, this would not be straightforward
- we could have specific fields that would be versioned and have own schema
  e.g. in case of Image builder job having some field that would introduce a nested schema
  and we could have different versions of these: e.g.

```yaml
- job: vm_image_build
    trigger: pull_request
    image_builder_metadata:
      version: 1
      image_request:
        packages_to_install: [packit]
        owner: packit
        project: packit-dev
      image_customizations:
        image_type: aws
        image_architecture: x86_64
        image_account_id: "727920394381"
```

```yaml
- job: vm_image_build
    trigger: pull_request
    image_builder_metadata:
      version: 2
      image_distribution: rhel-8
      image_type: aws
      image_architecture: x86_64
      image_account_id: "727920394381"
      packages_to_install: [packit]
      owner: packit
      project: packit-dev
```

and schemas:

```python
class ImageBuilderMetadataV1(ImageBuilderMetadataSchema):
    image_distribution = fields.String(missing=None)
    image_request = fields.Dict(missing=None)
    image_customizations = fields.Dict(missing=None)
```

```python
class ImageBuilderMetadataV2(ImageBuilderMetadataSchema):
    image_distribution = fields.String(missing=None)
    image_type: fields.String(missing=None)
    image_architecture = fields.String(missing=None)
    image_account_id = fields.String(missing=None)
    packages_to_install = fields.String(missing=None)
    owner = fields.String(missing=None)
    project = fields.String(missing=None)
```

and the config object would have all the fields and the code could handle both

- from the coding perspective this would not be a problem - the version would be detected either from whole config
  or directly from the `image_builder_metadata`
- but this may be confusing to users - versioning some configuration field apart from the whole config,
  - if we would do both whole config versioning and only fields versioning, this would become
    complicated and we would need to solve integration of both

## Implementation details for the whole config versioning

### Versioning

- for each backwards incompatible change, we would bump the version
- there would be a default version, options:
  - 1 - since 1 would be the version "before starting the versioning", it would be the most
    natural that if there is no version specified, the version is 1 (Docker does the same)
  - always the latest: we would need to enforce with introducing the first backwards incompatible change
    that all projects have the version set in their configs to 1 or use the changed schema (we could
    open PRs to projects with the config change, [see](https://github.com/packit/research/issues/159))
- this would be properly documented, we can get inspired by Docker,
  [see](https://docs.docker.com/compose/compose-file/compose-versioning/#versioning), the documentation
  would also include Packit version that starts supporting the particular configuration schema

### How this could work

- check the version in `PackageConfig.get_from_dict()` (use the default if not present)
- import the schema classes matching that version:

```python
if version == "1":
    from packit.schema.v1 import PackageConfigSchema
elif version == "2":
    from packit.schema.v2 import PackageConfigSchema
```

- this would allow partially redefining schema classes or reexporting existing schema classes, e.g. in `packit.schema.v2`:

```python
from packit.schema.v1 import PackageConfigSchema as PackageConfigSchemaV1
# reexport as v2, without a change
from packit.schema.v1 import JobConfig

class PackageConfigSchema(PackageConfigSchemaV1):
    # override some fields
```

- we would need to make sure that load-dump-load results in same representation
- config classes would not be versioned - all config schema versions need to be migrated when loading
  the configuration to the latest state of the configuration object

## Plan

- consider also relation to [this issue](https://github.com/packit/research/issues/159)
  - if we would introduce some change that would break the compatibility, we would open PRs for each repository that
    uses the particular configuration field
  - this could not be sufficient for all use cases
- decide whether we want to support versioning of only some fields
- decide what would be the default if version not specified in the config (and plan
  if we want to open PRs to existing projects with introducing `version` field and providing link to
  explaining documentation)
- with the next introduction of backwards incompatible change/ or right away, start versioning the schema
