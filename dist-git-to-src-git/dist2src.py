#!/usr/bin/python3

import functools
import logging
import os
import re
import shutil
import tempfile

import click
import git
import sh
from packit.config.package_config import get_local_specfile_path
from rebasehelper.specfile import SpecFile


logger = logging.getLogger(__name__)


@click.group("dist2src")
@click.option(
    "-v", "--verbose", count=True, help="Increase verbosity. Repeat to log more."
)
def cli(verbose):
    """Script to convert the tip of a branch from a dist-git repository
    into a commit on a branch in a source-git repository.

    As of now, this downloads the sources from the lookaside cache,
    unpacks them, applies all the patches, and remove the applied patches
    from the SPEC-file.

    For example to convert git.centos.org/rpms/rpm, branch 'c8s', to a
    source-git repo, with a branch also called 'c8s', in one step:

        \b
        $ cd git.centos.org
        $ dist2src convert rpms/rpm:c8s src/rpm:c8s

    For the same, but doing each conversion step separately:

        \b
        $ cd git.centos.org
        $ dist2src checkout rpms/rpm c8s
        $ dist2src get-archive rpms/rpm
        $ dist2src checkout --orphan src/rpm c8s
        $ dist2src extract-archive rpms/rpm src/rpm
        $ dist2src copy-spec rpms/rpm src/rpm
        $ dist2src copy-patches rpms/rpm src/rpm
        $ dist2src apply-patches src/rpm
        $ dist2src commit src/rpm
    """
    logger.addHandler(logging.StreamHandler())
    if verbose > 1:
        logger.setLevel(logging.DEBUG)
    elif verbose > 0:
        logger.setLevel(logging.INFO)


def log_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args_string = ", ".join([repr(a) for a in args])
        kwargs_string = ", ".join([f"{k}={v!r}" for k, v in kwargs.items()])
        sep = ", " if args_string and kwargs_string else ""
        logger.debug(f"{func.__name__}({args_string}{sep}{kwargs_string})")
        ret = func(*args, **kwargs)
        return ret
    return wrapper


@cli.command()
@click.argument("path")
@click.argument("branch")
@click.option(
    "--orphan", is_flag=True, help="Create an branch with disconnected history."
)
@log_call
def checkout(path, branch, orphan=False):
    """Checkout a Git repository.

    This will create the directory at PATH, if it doesn't exist already,
    and initialize it as a Git repository. The later is not destructive
    in an existing directory.

    Checking out BRANCH is done with the `-B` flag, which means the
    branch is created if it doesn't exist or reset, if it does.
    """
    if path.startswith(os.pardir):
        raise ValueError("This is bad, don't start path with '..'")

    if not os.path.exists(path):
        os.makedirs(path)

    repo = git.Repo.init(path)
    options = {}
    if orphan:
        options["orphan"] = branch

    if options:
        repo.git.checkout(**options)
    else:
        repo.git.checkout(branch)


@cli.command()
@click.argument("gitdir")
@log_call
def get_archive(gitdir):
    """Calls get_sources.sh in GITDIR.

    GITDIR needs to be a dist-git repository.

    Set DIST2SRC_GET_SOURCES to the path to git_sources.sh, if it's not
    in the PATH.
    """
    script = os.getenv("DIST2SRC_GET_SOURCES", "get_sources.sh")
    command = sh.Command(script)

    with sh.pushd(gitdir):
        logger.debug(f"Running command in {os.getcwd()}")
        stdout = command()

    return stdout


@cli.command()
@click.argument("origin")
@click.argument("dest")
@log_call
@click.pass_context
def copy_spec(ctx, origin, dest):
    """Copy the 'SPECS' directory from a dist-git repo to a source-git repo.

    In the source-git repo this is going to be under 'centos-packaging'.
    """
    shutil.copytree(
        os.path.join(origin, "SPECS"), os.path.join(dest, "centos-packaging", "SPECS")
    )


@cli.command()
@click.argument("origin")
@click.argument("dest")
@log_call
@click.pass_context
def copy_patches(ctx, origin, dest):
    """Find and copy patches from a dist-git repo to a source-git repo.

    This looks for 'SOURCES/*.patch' in ORIGIN and copy everything found to
    'centos-packaging/SOURCES/' in DEST.
    """
    files = filter(
        lambda x: x.endswith(".patch"), os.listdir(os.path.join(origin, "SOURCES"))
    )
    os.makedirs(os.path.join(dest, "centos-packaging", "SOURCES"), exist_ok=True)
    for f in files:
        shutil.copy2(
            os.path.join(origin, "SOURCES", f),
            os.path.join(dest, "centos-packaging", "SOURCES", f),
        )


@cli.command()
@click.argument("origin")
@click.argument("dest")
@log_call
@click.pass_context
def extract_archive(ctx, origin, dest):
    """Extract the source archive found in ORIGIN to DEST.

    First, make sure that the archive was downloaded.

    After extracting the archive, stage and commit the changes in DEST.
    """
    # Make sure, the archive exists and use the STDOUT of get_sources.sh
    # to find out its path.
    stdout = ""
    while "exists" not in stdout:
        stdout = ctx.invoke(get_archive, gitdir=origin)
    archive = os.path.join(origin, stdout.partition(" exists")[0])

    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.unpack_archive(archive, tmpdir)
        # Expect an archive with a single directory.
        assert len(os.listdir(tmpdir)) == 1
        topdir = os.path.join(tmpdir, os.listdir(tmpdir)[0])
        # These are all the files under the directory that was
        # in the archive.
        files = os.listdir(topdir)
        for f in files:
            shutil.move(os.path.join(topdir, f), os.path.join(dest, f))

    ctx.invoke(stage, gitdir=dest)
    ctx.invoke(commit, m="Unpack archive", gitdir=dest)


@cli.command()
@click.argument("gitdir")
@log_call
@click.pass_context
def apply_patches(ctx, gitdir):
    """Apply the patches used in the SPEC-file found in GITDIR.

    Apply all the patches used in the SPEC-file, then update the
    SPEC-file by commenting the patches that were applied and deleting
    those patches from the disk.

    Stage and commit changes after each patch, except the ones in the
    'centos-packaging' directory.
    """

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

    specdir = os.path.join(gitdir, "centos-packaging", "SPECS")
    specpath = os.path.join(specdir, get_local_specfile_path([specdir]))
    logger.info(f"specpath = {specpath}")
    specfile = Specfile(
        specpath, sources_location=os.path.join(gitdir, "centos-packaging", "SOURCES"),
    )
    repo = git.Repo(gitdir)

    for patch in specfile.get_applied_patches():
        message = f"Apply Patch{patch.index}: {patch.get_patch_name()}"
        logger.info(message)
        rel_path = os.path.relpath(patch.path, gitdir)
        try:
            repo.git.am(rel_path)
        except git.exc.CommandError as e:
            logger.debug(str(e))
            repo.git.apply(rel_path, p=patch.strip)
            ctx.invoke(stage, gitdir=gitdir, exclude="centos-packaging")
            ctx.invoke(commit, gitdir=gitdir, m=message)

        # The patch is a commit now, so clean it up.
        os.unlink(patch.path)
        # TODO(csomh):
        # the bellow is not complete, as there are many more ways to specify
        # patches in spec files. Cover this in the future.
        specfile.comment_patches([patch.index])
        specfile._process_patches([patch.index])
        specfile.save()


@cli.command()
@click.argument("gitdir")
@click.option("-m", default="Import sources from dist-git", help="Git commmit message")
@log_call
def commit(gitdir, m):
    """Commit staged changes in GITDIR."""
    repo = git.Repo(gitdir)
    repo.git.commit(m=m)


@cli.command()
@click.argument("gitdir")
@click.option("--exclude", help="Path to exclude from staging, relative to GITDIR")
@log_call
def stage(gitdir, exclude=None):
    """Stage content in GITDIR."""
    repo = git.Repo(gitdir)
    if exclude:
        exclude = f":(exclude){exclude}"
        logger.debug(exclude)
    repo.git.add(".", exclude)


@cli.command()
@click.argument("origin")
@click.argument("dest")
@log_call
@click.pass_context
def convert(ctx, origin, dest):
    """Convert a dist-git repository into a source-git repository.

    ORIGIN and DEST are in the format of

        REPO_PATH:BRANCH

    This command calls all the other commands.
    """
    origin_dir, origin_branch = origin.split(":")
    dest_dir, dest_branch = dest.split(":")

    ctx.invoke(checkout, path=origin_dir, branch=origin_branch)
    ctx.invoke(get_archive, gitdir=origin_dir)
    ctx.invoke(checkout, path=dest_dir, branch=dest_branch, orphan=True)
    ctx.invoke(extract_archive, origin=origin_dir, dest=dest_dir)
    ctx.invoke(copy_spec, origin=origin_dir, dest=dest_dir)
    ctx.invoke(copy_patches, origin=origin_dir, dest=dest_dir)
    ctx.invoke(apply_patches, gitdir=dest_dir)
    ctx.invoke(stage, gitdir=dest_dir)
    ctx.invoke(commit, gitdir=dest_dir, m="Add downstream SPEC-file")


if __name__ == "__main__":
    cli()
