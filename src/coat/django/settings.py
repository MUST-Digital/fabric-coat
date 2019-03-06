from django.core.validators import (
    MinLengthValidator, RegexValidator
)

from coat.settings import Settings


__all__ = ("DjangoSettings", "VirtualEnvSettings")


class VirtualEnvSettings(Settings):
    """
    A settings object for a python virtualenv based envorinment.
    """
    DEFAULT_ACTIVATOR = 'source {dir}/bin/activate'

    DEFAULT_COMMANDS = [
        "pip -q install -r django/requirements.txt"
    ]

    DEFAULT_INIT_COMMANDS = [
        "virtualenv %(env_dir)s"
    ]

    defaults = {
        'activator': DEFAULT_ACTIVATOR,
        'commands': DEFAULT_COMMANDS,
        'init_commands': DEFAULT_INIT_COMMANDS,
    }

    required = {
        'env_dir': MinLengthValidator(1),
    }


class DjangoSettings(Settings):
    """
    A settings object for a Django project.
    """
    DEFAULT_MANAGEMENT_COMMANDS = [
        "migrate --noinput",
        "collectstatic --noinput --verbosity 0",
    ]

    defaults = {
        'management_commands': DEFAULT_MANAGEMENT_COMMANDS,
        'versions_dir': 'app/versions',
    }

    required = {
        # 'settings_file': RegexValidator(
        #     "^localsettings_(\w+)\.py$",
        #     "localsettings file must be defined and named localsettings_ENV.py"
        # ),
        'settings_file': RegexValidator(
            "^production\.py$",
            "production settings file must be defined and named production.py"
        ),
    }
