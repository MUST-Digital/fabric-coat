from django.core.exceptions import ValidationError

from fabric.utils import abort, _AttributeDict


class Settings(_AttributeDict):
    """
    Object that holds setting items and a method of validating required
    settings.

    The class should be subclassed and the key `defaults` should contain a dict
    with default values.

    The dict `required` should contain key => (`validator`, ...) where
    `validator` is a callable that will be called with the value to be
    validated.
    """
    def __init__(self, **kwargs):
        super(Settings, self).__init__()

        self.update(self.defaults)
        self.update(kwargs)

    def resolve_all_keys(self):
        def replace(v):
            """
            Recursivly replace strings, dicts, tuples and lists.
            """
            if isinstance(v, (tuple, list)):
                return map(replace, v)
            elif isinstance(v, dict):
                for key, value in v.iteritems():
                    v[replace(key)] = replace(value)
                return v
            elif isinstance(v, basestring):
                return v % self
            else:
                return v

        for key, value in self.iteritems():
            self[key] = replace(value)

    def validate_or_abort(self):
        """
        Validate the values acording to the list of validators given.

        Also resolves all values if validation was successful.
        """
        missing = []

        for key, validators in self.required.iteritems():
            if not isinstance(validators, (list, tuple)):
                validators = (validators, )

            for validator in validators:
                try:
                    validator(self[key])
                except KeyError:
                    missing.append("* %s was not defined" % key)
                except ValueError as exc:
                    missing.append("* %s caused ValueError(%s)" % (key, exc))
                except ValidationError as exc:
                    missing.append("* %s failed validation - %s" % (
                        key, "\n  * ".join(exc.messages)
                    ))

        if len(missing) > 0:
            abort(
                "missing (or invalid) settings:\n\n" + ("\n".join(missing))
            )

        self.resolve_all_keys()
