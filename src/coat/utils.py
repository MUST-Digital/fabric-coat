import os
import atexit
import shutil
import tempfile

from pydispatch import dispatcher
from fabric.state import env
from fabric.api import lcd, local, hide, settings, cd, run
from fabric.contrib import files as fabric_files
from coat import signals


def get_project_root_directory():
    """
    Returns the dirname of the fabfile.
    """
    return os.path.dirname(os.path.abspath(env.real_fabfile))


def workdir_prepare_checkout(revision, folders):
    """
    Returns an absolute path to a directory containing a git checkout of the
    given treeish revision.

    Registers a hook with atexit to delete the returned directory.

    Dispatches signals to pre_workdir_checkout and post_workdir_checkout.
    """
    dispatcher.send(
        signal=signals.pre_workdir_prepare_checkout,
        sender=workdir_prepare_checkout,
        revision=revision,
    )

    workdir = tempfile.mkdtemp()

    atexit.register(shutil.rmtree, workdir, True)

    with lcd(get_project_root_directory()):
        local("git archive %s %s | tar -x -C %s" %
              (revision, " ".join(folders), workdir))

        dispatcher.send(
            signal=signals.post_workdir_prepare_checkout,
            sender=workdir_prepare_checkout,
            revision=revision,
            workdir=workdir,
        )

    return workdir


def local_resolve_revision(revision):
    """
    Returns a partial sha1 from a treeish revision.
    """
    with lcd(get_project_root_directory()):
        with hide("running"):
            revision = local("git log -1 --format=%%h %s" % revision,
                             capture=True)

    return revision


def remote_absolute_path(path):
    """
    Returns an absolute path built of joining remote_pwd and base_dir with
    path. If either is an absolute path, it will be used returned.

    Must be used everywhere a remote path is used.
    """
    return os.path.join(env.remote_pwd, env.base_dir, path)


def remote_resolve_current_revision():
    """
    Returns the locally resolved currently active remote revision.
    """
    revision = None

    with settings(hide("stderr", "running", "stdout", "warnings"),
                  warn_only=True):

        # make sure version_dir exists
        versions_dir = remote_absolute_path(env.django_settings.versions_dir)

        if not fabric_files.exists(versions_dir):
            run("mkdir -p %s" % versions_dir)

        # try to resolve current symlink
        with cd(versions_dir):
            if fabric_files.exists("current"):
                revision = run("readlink current")

                if not revision.failed:
                    revision = revision.rstrip("/")

    if revision:
        return local_resolve_revision(revision)
