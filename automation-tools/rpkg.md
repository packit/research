# RPKG

- It is an rpm packaging utility that works with both DistGit and standard Git repositories and it handles two types of directory content: packed and unpacked.
- [ :computer: pagure.io/rpkg-util](https://pagure.io/rpkg-util)
- ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rpkg.svg), [![PyPI](https://img.shields.io/pypi/v/rpkg.svg)](https://pypi.org/project/rpkg/), [ :package: fedora packages](https://src.fedoraproject.org/rpms/rpkg)


:heavy_plus_sign:
- from the *template specfile* you can generate:
  - specfile (changelog from commits)
  - srpm
  - rpm
- generation can be done from dirty repo as well as per commit
- automatic commit suffixes for files (sources, `srpm`, `rpm`)
- push to copr
- multipackage support
- looks [active](https://pagure.io/rpkg-util/commits/master)

:heavy_minus_sign:
- autopacking workflow is deprecated
- need to write *template specfile*

### Specfile template

```
Name:       {{{ git_dir_name }}}
Version:    {{{ git_dir_version }}}
Release:    1%{?dist}
Summary:    This is a test package.

License:    GPLv2+
URL:        https://someurl.org
VCS:        {{{ git_dir_vcs }}}

Source:     {{{ git_dir_pack }}}

%description
This is a test package.

%prep
{{{ git_dir_setup_macro }}}

%changelog
{{{ git_dir_changelog }}}
```



### Other sources

- [Spec templates from scratch](https://docs.pagure.org/rpkg-util/spec_templates_from_scratch.html)
- [Quick start: New project](https://docs.pagure.org/rpkg-util/quick_start.html) ([Existing project](https://docs.pagure.org/rpkg-util/quick_start.html#existing-project))
