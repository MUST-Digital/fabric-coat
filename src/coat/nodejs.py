from fabric.api import run, local, cd, settings, prefix, hide
from fabric.operations import require
from fabric.state import env

from coat import utils as coat_utils
from coat.django.commands import copy_revision_to_remote, remote_activate_revision
from coat.settings import Settings

class NodeVirtualEnvSettings(Settings):
    """
    A settings object for a python virtualenv based envorinment.
    """
    DEFAULT_ACTIVATOR = 'source {dir}/bin/activate'

    DEFAULT_COMMANDS = [
    ]

    DEFAULT_INIT_COMMANDS = [
        "virtualenv %(env_dir)s"
    ]

    defaults = {
        'activator': DEFAULT_ACTIVATOR,
        'commands': DEFAULT_COMMANDS,
        'init_commands': DEFAULT_INIT_COMMANDS,
    }

    required = {}

    def validate_or_abort(self):
        """
        Validate the values acording to the list of validators given.

        Also resolves all values if validation was successful.
        """
        missing = []

        for key, validators in self.required.items():
            if not isinstance(validators, (list, tuple)):
                validators = (validators, )

            for validator in validators:
                try:
                    validator(self[key])
                except KeyError:
                    missing.append("* %s was not defined" % key)
                except ValueError as exc:
                    missing.append("* %s caused ValueError(%s)" % (key, exc))

        if len(missing) > 0:
            abort(
                "missing (or invalid) settings:\n\n" + ("\n".join(missing))
            )

        self.resolve_all_keys()

class NodeSettings(Settings):
    """
    A settings object for a Django project.
    """
    defaults = {
        'versions_dir': 'app/versions',
    }

    required = {
    }

def deploy(revision="master"):
    require("base_dir", "virtualenv_settings",
            provided_by=("env_test", "env_live"))

    env.remote_pwd = run("pwd")

    env.virtualenv_settings.validate_or_abort()

    env.remote_revision = coat_utils.remote_resolve_current_revision(is_django=False)
    env.deploy_revision = coat_utils.local_resolve_revision(revision)
    env.deploy_workdir = coat_utils.workdir_prepare_checkout(
        revision, folders=(env.get('project_name', ''), )
    )

    copy_revision_to_remote(
        env.deploy_workdir, env.remote_revision, env.deploy_revision,
        is_django=False
    )

    remote_activate_revision(
        env.deploy_workdir, env.remote_revision, env.deploy_revision,
        is_django=False
    )
