---
title: Fedora package candidates for source-git
authors: ttomecek
---

This research crams through [all fedora spec files](https://pkgs.fedoraproject.org/repo/rpm-specs-latest.tar.xz) to find out:

- Packages with most downstream patches
- If they use %autosetup, %setup, %patch, %autopatch
- How often they were updated in F34

The research was done using [a jupyter notebook](https://jupyter.org/).

Let's navigate to the [directory](https://github.com/packit/research/tree/main/research/fedora-spec-files) with this research to visualize the data.

```
$ cd fedora-spec-files
```

## Installation

A Containerfile is provided with a list of all dependencies so we can gather and visualize the data. Let's build it:

```
$ make build

COMMIT fedora-spec-research
--> 525fd72aeba
Successfully tagged localhost/fedora-spec-research:latest
525fd72aebaeda0e4648bad7646d9169f81b7ab541ffebc76312c35faa10da7f
```

## Usage

Once built, we need to gather data about the packages:

```
$ make generate-data
```

You can rerun this step any time you want. The data is saved as `data.json`.

Once the file is available, we can run jupyter:

```
$ make run
```

Open the given link in your browser and navigate to notebook "fedora-spec-files.ipynb".

You should now click Kernel > "Restart & Run All" to see the current data visualized.
