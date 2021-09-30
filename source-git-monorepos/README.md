# Support monorepos in source-git

Monorepos store the source code of multiple projects in a single
repository. They are a special use-case from a source-git point of view,
because an upstream monorepo maps to multiple dist-git repositories in the
distribution.

One example for the above is [LLVM] from which code flows into multiple
dist-git repositories in Fedora Linux.

Currently the source-git commands in source-git map an upstream repo to a
single dist-git repo in the distribution.

To change this, a mechanism to specify which path(s) in the monorepo to map to
which dist-git repo in the distribution should be introduced.

This could be done by introducing a list-type `packages` key. Items of the
list are objects with keys identical to the current top-level keys in
`source-git.yaml`, except `upstream_project_url` and `upstream_ref`—these
are left to be top-level keys only, and a new `package_paths` key which is a
list of paths in the monorepo which map to the dist-git repo specified by
`downstream_package_name`. Packit limits patch generation to these paths.

Example:

```yaml
upstream_project_url: https://github.com/llvm/llvm-project.git
upstream_ref: llvmorg-13.0.0-rc3
packages:
  - downstream_package_name: python-lit
    specfile_path: .distro/python-lit/python-lit.spec
    package_paths:
      - llvm/utils/lit
    # This could be also used, but it's not required here.
    # patch_generation_ignore_paths:
    # - .distro
    sync_changelog: true
    synced_files:
      - src: .distro/python-lit/
        dest: .
        delete: true
        filters:
          - protect .git*
          - protect sources
          - exclude .gitignore
    sources:
      - path: lit-13.0.0rc1
        url: https://src.fedoraproject.org/repo/pkgs/rpms/python-lit/lit-13.0.0rc1/sha512/000a6875d371793ccab7f9c7af0e5906d1d98bb8ff09b297b7f0978c083ec05acb48fd8dbd1647bc9ba6548c8c629cc693219ce8d247877eab14ff250e46cfed/lit-13.0.0rc1
```

With the above source-git configuration could be kept in
`.distro/source-git.yaml`. Downstream files to be synced to dist-git are to be
kept in subdirectories, named according to the distro package, in `.distro` to
keep things organized.

This way all distribution configs and files would be kept at one place, which
probably is somewhat better than having source-git configuration spread
across the monorepo, in subdirectories. This setup also allows multiple paths
from the repo mapped to a dist-git repo.

For **backwards compatibility**: if the top-level `packages` key is missing,
source-git configuration is read as currently is.

- TODO Can archives stored in the dist-git repositories mapped to one or more
  paths in the upstream repo?
- TODO Is support needed to have different packages generated from different
  git refs? (This would defy the point in having a monorepo, but some might
  require it.)

[llvm]: https://github.com/llvm/llvm-project
