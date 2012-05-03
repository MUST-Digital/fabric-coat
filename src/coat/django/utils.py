import os


def find_manage(basedir):
    """
    Returns the path to manage.py relative to `basedir`.
    """
    for root, dirs, files in os.walk(basedir):
        if 'manage.py' in files:
            return os.path.join(root, 'manage.py')


def find_django_appname(basedir):
    """
    Returns the django application name.
    """
    for root, dirs, files in os.walk(basedir):
        if 'settings.py' in files:
            return root.split("/")[-1]