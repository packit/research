---
title: Onboard automation scripts
authors:
  - dhodovsk
  - phracek
  - ttomecek
  - flachman
  -
---

`input_packages.yml`

- Input for `onboard.py` script. List of packages that are going to be onboarded with the script.

Accepted format is list of YAML dicts:

```
-
  downstream_name: ogr
  upstream_url: "git@github.com:packit-service/ogr.git"
-
  downstream_name: packit
  upstream_url: "https://github.com/packit-service/packit"
```

`onboard.py`

- For every package in `input_packages.yml`, the script:

1.  Clones upstream repository
2.  Makes sure packit configuration is present. If it is not,
    generates it using `packit generate`
3.  Runs `packit status`
4.  Tries building srpm with upstream specfile
5.  Tries building srpm with downstream specfile

- Script stores all the log output in the `./output` directory, where every instance
  of run is stored in separate directory marked by date.
- The directory contains logs separated by package name and results.yml file with the results for all packages.
- Run the script using:

```
python3 onboard.py
```
