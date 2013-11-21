from __future__ import with_statement

import os
import re
import tempfile
import time
import shutil

from datetime import datetime

from fabric.api import run, local, get, cd, lcd, put
from fabric.state import env
from fabric.operations import require
from fabric.contrib.console import confirm

__all__ = ("update_env", "download_uploads_from_remote",
           "upload_uploads_to_remote", "download_database_from_remote",
           "update_database_from_remote", "update_database_on_remote",
           "deploy")


def get_local_base_dir():
    return os.path.dirname(os.path.abspath(env.real_fabfile))


def backup_prune():
    if not env.backup_path:
        return

    backup_path = os.path.join(env.local_base_dir, env.backup_path)

    if not os.path.exists(backup_path):
        return

    wanted = []

    for entry in os.listdir(backup_path):
        if entry.startswith("."):
            continue

        absentry = os.path.join(backup_path, entry)

        if time.time() - os.path.getctime(absentry) > 43200:
            wanted.append(absentry)

    for entry in wanted:
        shutil.rmtree(entry)


def backup_create_local(local_source):
    backup_prune()

    backup_target = os.path.join(env.local_base_dir,
                                 env.backup_path,
                                 env.backup_prefix)

    if os.path.isdir(local_source):
        backup_target = os.path.join(backup_target, local_source)

    local("mkdir -p %s" % backup_target)

    local("rsync -a --link-dest=%s %s %s" % (
        local_source, local_source, backup_target)
    )


def update_env(*args, **kwargs):
    env.wordpress_path = "public_html"
    env.backup_prefix = "%Y%m%d-%H%m%S"
    env.backup_path = "backups"

    env.update(kwargs)

    if 'local_base_dir' not in env:
        env.local_base_dir = get_local_base_dir()

    if env.backup_prefix:
        env.backup_prefix = datetime.now().strftime(env.backup_prefix)


def parse_config_from_file(settings_file):
    lines = open(settings_file).read()

    define_re = re.compile(r"""define\(["'](?P<key>[^'"]+)["'],\s*["'](?P<value>[^'"]*)["']\)""", re.S | re.M)

    return dict(define_re.findall(lines))


def read_config():
    """
    Returns a dict of the current local and remote wordpress settings.
    """
    wordpress_path = os.path.join(env.local_base_dir, env.local_wordpress_path)

    return {
        'local': parse_config_from_file(os.path.join(wordpress_path, "wp-config.php")),
        'remote': parse_config_from_file(os.path.join(wordpress_path, env.settings_file))
    }


def download_uploads_from_remote():
    require("base_dir", provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    with lcd(os.path.join(env.local_base_dir, env.local_wordpress_path)):
        backup_create_local("wp-content/uploads")

        local("rsync -a "
              "%(user)s@%(host)s:%(base_dir)s/%(wordpress_path)s/wp-content/uploads/ "
              "wp-content/uploads/" % env)


def upload_uploads_to_remote():
    require("base_dir", provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    confirm("This will override data on remote. Are you sure?", default=False)

    with lcd(os.path.join(env.local_base_dir, env.local_wordpress_path)):
        local("rsync -a wp-content/uploads/* "
              "%(user)s@%(host)s:%(base_dir)s/%(wordpress_path)s/wp-content/uploads/" % env)


def download_database_from_remote():
    require("base_dir", provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    wp_config = read_config()

    run("mysqldump -u%(DB_USER)s -p\"%(DB_PASSWORD)s\" -h%(DB_HOST)s --add-drop-table %(DB_NAME)s > /tmp/%(DB_USER)s.sql" % wp_config['remote'])
    get("/tmp/%(DB_USER)s.sql" % wp_config['remote'], os.path.join(env.local_base_path, env.local_wordpress_path, "%(DB_USER)s.sql" % wp_config['remote']))
    run("rm -f /tmp/%(DB_USER)s.sql" % wp_config['remote'])


def update_database_from_remote():
    require("base_dir", provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    wp_config = read_config()
    dump_filename = "/tmp/%(DB_USER)s_%(DB_NAME)s.sql" % wp_config['remote']

    wp_config['remote']['dump_filename'] = dump_filename
    wp_config['local']['dump_filename'] = dump_filename

    with lcd(env.local_base_dir):
        local("mysqldump -u%(DB_USER)s -p\"%(DB_PASSWORD)s\" -h%(DB_HOST)s --add-drop-table %(DB_NAME)s | gzip > %(DB_NAME)s.sql.gz" % wp_config['local'])

        backup_create_local("%(DB_NAME)s.sql.gz" % wp_config['local'])

        run("rm -f %(DB_NAME)s.sql.gz" % wp_config['local'])

    run("mysqldump -u%(DB_USER)s -p\"%(DB_PASSWORD)s\" -h%(DB_HOST)s --add-drop-table %(DB_NAME)s > %(dump_filename)s" % wp_config['remote'])
    get(dump_filename, dump_filename)
    run("rm -f %s" % dump_filename)

    local("mysql -u%(DB_USER)s -p\"%(DB_PASSWORD)s\" -h%(DB_HOST)s %(DB_NAME)s < %(dump_filename)s" % wp_config['local'])

    os.unlink(dump_filename)


def update_database_on_remote():
    require("base_dir", provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    confirm("This will override data on remote. Are you sure?", default=False)

    wp_config = read_config()

    local("mysqldump -u%(DB_USER)s -p\"%(DB_PASSWORD)s\" -h%(DB_HOST)s --add-drop-table %(DB_NAME)s > /tmp/%(DB_USER)s.sql" % wp_config['local'])
    put("/tmp/%(DB_USER)s.sql" % wp_config['local'], "/tmp/%(DB_USER)s.sql" % wp_config['remote'])
    os.unlink("/tmp/%(DB_USER)s.sql" % wp_config['local'])

    wp_config['remote']['backup_name'] = "%(DB_USER)s_%(DB_NAME)s" % wp_config['remote']

    run("mysqldump -u%(DB_USER)s -p\"%(DB_PASSWORD)s\" -h%(DB_HOST)s --add-drop-table %(DB_NAME)s | gzip > /tmp/%(backup_name)s.sql.gz" % wp_config['remote'])

    run("mysql -u%(DB_USER)s -p\"%(DB_PASSWORD)s\" -h%(DB_HOST)s %(DB_NAME)s < /tmp/%(DB_USER)s.sql" % wp_config['remote'])
    run("rm -f /tmp/%(DB_USER)s.sql" % wp_config['remote'])


def deploy(revision="master", preprocessor=None):
    require('base_dir', provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    deploy_archive_dir = tempfile.mkdtemp()

    with lcd(env.local_base_dir):
        local('git archive %s %s | tar -x -f- -C %s' % (revision, env.local_wordpress_path, deploy_archive_dir))

        if preprocessor:
            preprocessor()

    local('rsync -a --exclude wp-config.php --exclude wp-content/uploads/* %s/%s/* %s@%s:%s/%s' %
          (deploy_archive_dir, env.local_wordpress_path, env.user, env.host,
           env.base_dir, env.wordpress_path))

    with cd(os.path.join(env.base_dir, env.wordpress_path)):
        if env.settings_file:
            run('cp %s wp-config.php' % env.settings_file)

    shutil.rmtree(deploy_archive_dir)
