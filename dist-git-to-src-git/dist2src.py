#!/usr/bin/python3

import os
import tarfile
import click
import git
import logging
import sh
from time import sleep


logger = logging.getLogger(__name__)


@click.group("dist2src")
@click.option("-v", "--verbose", count=True)
def cli(verbose):
    logger.addHandler(logging.StreamHandler())
    if verbose > 1:
        logger.setLevel(logging.DEBUG)
    elif verbose > 0:
        logger.setLevel(logging.INFO)


@cli.command()
@click.argument("path")
@click.argument("branch")
@click.option("--orphan", is_flag=True, help="Create an branch with disconnected history.")
def checkout(path, branch, orphan=False):
    if path.startswith(os.pardir):
        raise ValueError("This is bad, don't start path with '..'")

    if not os.path.exists(path):
        os.makedirs(path)

    repo = git.Repo.init(path)
    options = {}
    if orphan:
        options["orphan"] = branch
    else:
        options["B"] = branch

    repo.git.checkout(**options)


@cli.command()
@click.argument("path")
def get_archive(path):
    # TODO(csomh): make the path to get_sources.sh configurable
    get_sources = sh.Command("get_sources.sh")
    with sh.pushd(path):
        get_sources()


@cli.command()
@click.argument("origin")
@click.argument("dest")
@click.pass_context
def copy_spec(ctx, origin, dest):
    import shutil
    shutil.copytree(os.path.join(origin, "SPECS"), os.path.join(dest, "centos-packaging", "SPECS"))
    ctx.invoke(stage, gitdir=dest)


@cli.command()
@click.argument("origin")
@click.argument("dest")
@click.pass_context
def copy_patches(ctx, origin, dest):
    import shutil
    files = filter(lambda x: x.endswith(".patch"), os.listdir(os.path.join(origin, "SOURCES")))
    os.makedirs(os.path.join(dest, "centos-packaging", "SOURCES"), exist_ok=True)
    for f in files:
        shutil.copy2(os.path.join(origin, "SOURCES", f), os.path.join(dest, "centos-packaging", "SOURCES", f))
    ctx.invoke(stage, gitdir=dest)


@cli.command()
@click.argument("origin")
@click.argument("dest")
@click.pass_context
def extract_archive(ctx, origin, dest):
    import tempfile
    import shutil

    get_sources = sh.Command("get_sources.sh")
    stdout = ""
    while "exists" not in stdout:
        with sh.pushd(origin):
            stdout = get_sources()
    archive = os.path.join(origin, stdout.partition(" exists")[0])
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.unpack_archive(archive, tmpdir)
        assert len(os.listdir(tmpdir)) == 1
        topdir = os.path.join(tmpdir, os.listdir(tmpdir)[0])
        files = os.listdir(topdir)
        for f in files:
            shutil.move(os.path.join(topdir, f), os.path.join(dest, f))
    ctx.invoke(stage, gitdir=dest)


@cli.command()
@click.argument("gitdir")
@click.pass_context
def apply_patches(ctx, gitdir):
    """Apply the patches defined in the spec file"""
    from rebasehelper.specfile import SpecFile
    import re

    class Specfile(SpecFile):
        def comment_patches(self, patch_indexes):
            pattern = re.compile(r"^Patch(?P<index>\d+)\s*:.+$")
            package = self.spec_content.section("%package")
            for i, line in enumerate(package):
                match = pattern.match(line)
                if match:
                    index = int(match.group("index"))
                    if index in patch_indexes:
                        logger.debug(f"Commenting patch {index}")
                        package[i] = f"# {line}"
            self.spec_content.replace_section("%package", package)


    specfile = Specfile(
        # TODO(csomh):
        # - Take spec file from packit.yaml?
        os.path.join(gitdir, "centos-packaging", "SPECS", "rpm.spec"),
        sources_location=os.path.join(gitdir, "centos-packaging", "SOURCES"),
    )
    repo = git.Repo(gitdir)

    to_be_removed = []
    delete = []
    for patch in specfile.get_applied_patches():
        logger.info(f"Apply Patch{patch.index}: {patch.get_patch_name()}")
        repo.git.apply(os.path.relpath(patch.path, gitdir), p=patch.strip)
        delete.append(patch.path)
        to_be_removed.append(patch.index)

    logger.info(f"Number of patches to be commented: {len(to_be_removed)}")
    # TODO(csomh):
    # the bellow is not complete, as there are many more ways to apply
    # patches in spec files. Cover this in the future.
    specfile.comment_patches(to_be_removed)
    specfile._process_patches(comment_out=to_be_removed)
    specfile.save()
    for p in delete:
        os.unlink(p)
    ctx.invoke(stage, gitdir=gitdir)

@cli.command()
@click.argument("gitdir")
def commit(gitdir):
    repo = git.Repo(gitdir)
    repo.git.commit(m="Import sources from dist-git")

@cli.command()
@click.argument("gitdir")
def stage(gitdir):
    repo = git.Repo(gitdir)
    repo.git.add(".")

@cli.command()
@click.argument("origin")
@click.argument("dest")
@click.pass_context
def convert(ctx, origin, dest):
    origin_dir, origin_branch = origin.split(":")
    dest_dir, dest_branch = dest.split(":")

    ctx.invoke(checkout, path=origin_dir, branch=origin_branch)
    ctx.invoke(get_archive, path=origin_dir)
    ctx.invoke(checkout, path=dest_dir, branch=dest_branch, orphan=True)
    ctx.invoke(extract_archive, origin=origin_dir, dest=dest_dir)
    ctx.invoke(copy_spec, origin=origin_dir, dest=dest_dir)
    ctx.invoke(copy_patches, origin=origin_dir, dest=dest_dir)
    ctx.invoke(apply_patches, gitdir=dest_dir)
    ctx.invoke(commit, gitdir=dest_dir)

if __name__ == "__main__":
    cli()
