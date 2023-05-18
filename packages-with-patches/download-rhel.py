#!/usr/bin/python3

import click
import re
import requests
from urllib.parse import urljoin
from pathlib import Path

CGIT = "https://pkgs.devel.redhat.com/cgit"
# repositories starting with these prefixes are (probably) not RHEL packages
IGNORE_PREFIXES = [
    "Application-",
    "Application_",
    "CloudForms-",
    "Engineering_",
    "Fuse_",
    "Hosted_",
    "IEEE_",
    "Internal-",
    "JBoss_",
    "OpenShift-",
    "OpenShift_",
    "Partner_",
    "Policy-",
    "Product_",
    "RedHat_",
    "Red_Hat_",
    "Release_",
    "Report-",
]
REPO_LINK = re.compile(
    "<tr><td class='toplevel-repo'><a title='.+?' href='(?P<url>.+?)'>rpms/(?P<name>.+?)</a></td>"
)
SPECFILE = re.compile(
    "<tr><td class='ls-mode'>.+?<a class='ls-blob spec' href='(?P<spec_url>.+?)'>"
)


def any_branch(url, branches):
    """Check if a repo on a given URL has at least one of the branches

    Args:
        url: URL of the repo
        branches: list of branches to be checked
    Returns:
        The name of the branch from branches which is found the last
    """
    ret = None
    for branch in branches:
        response = requests.get(f"{url}log/?h={branch}")
        if response.ok:
            ret = branch
    return ret


def search_spec(url, branch):
    tree_url = f"{url}tree/?h={branch}"
    response = requests.get(tree_url)
    response.raise_for_status()
    content = response.content.decode()
    for line in content.splitlines():
        match = SPECFILE.match(line)
        if match:
            spec_url = match.group("spec_url").replace("tree/", "plain/")
            response = requests.get(urljoin(CGIT, spec_url))
            response.raise_for_status()
            return response.content.decode()
    return None


def get_spec(url, branch, name):
    spec_url = f"{url}plain/{name}.spec?h={branch}"
    response = requests.get(spec_url)
    if not response.ok:
        spec = search_spec(url, branch)
    else:
        spec = response.content.decode()
    return spec


@click.command()
@click.argument("branches", nargs=-1, required=True)
@click.argument("output", nargs=1)
@click.option(
    "--offset",
    default=0,
    show_default=True,
    help="Start downloading specfiles from this offset, "
    "i.e. skip the specified number of repositories.",
)
@click.option(
    "--continue-from",
    default=None,
    help="Download specfiles starting with this repository.",
)
def download_rhel(branches, output, offset, continue_from):
    """Download specfiles by scraping the cgit pages."""
    Path(output).mkdir(parents=True, exist_ok=True)
    while True:
        response = requests.get(f"{CGIT}/rpms?ofs={offset}")
        response.raise_for_status()
        content = response.content.decode()
        if "toplevel-repo" not in content:
            break
        for line in content.splitlines():
            match = REPO_LINK.match(line)
            if not match:
                continue
            url, name = match.group("url", "name")
            if continue_from and continue_from != name:
                continue
            continue_from = None
            url = urljoin(CGIT, url)
            print(".", end="", flush=True)
            if (
                not any(name.startswith(prefix) for prefix in IGNORE_PREFIXES)
                and (branch := any_branch(url, branches))
                and (spec := get_spec(url, branch, name))
            ):
                print()
                print(name, url, sep=": ")
                with open(f"{output}/{name}.spec", "w") as fp:
                    fp.write(spec)
        offset += 5000
        print(offset)


if __name__ == "__main__":
    download_rhel()
