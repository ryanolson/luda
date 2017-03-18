# -*- coding: utf-8 -*-

import click
import os
import subprocess

from luda import which, Volume, add_display

PathType = click.Path(exists=True, file_okay=True,
                      dir_okay=True, resolve_path=True)

# ideas from:
# https://denibertovic.com/posts/handling-permissions-with-docker-volumes/

# volumes have the same syntax as docker volumes; however,
# - relative paths can be resolved
# - if no mount path is given, the basename of the host path is used, eg
#   /basename(hostpath)
#
# Examples:
# --volume /path/data:/data:ro
# --volume data:/data:ro
# --volume data::ro

# create init/entrypoint script to gnerate a user with a uid inside the
# contaienr
# 1) create temp dire with templated init script
# 2) volume mount tmp dir to /bootstrap
# 3) set --entrypoint to /bootstrap/init.sh
# #
# # Package


class DockerVolumeType(click.ParamType):
    name = 'volume'

    def convert(self, value, param, ctx):
        return Volume(*value.split(":"))


@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.option("--work", type=PathType, default=os.getcwd())
@click.option("-v", "--volume", type=DockerVolumeType(), multiple=True)
@click.option('--display', is_flag=True)
@click.option('--docker', is_flag=True)
@click.option('--dev', is_flag=True)
@click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)
def main(docker_args, display, docker, dev, work=None, volume=None):
    """Console script for luda"""

    # get some data about the user: name, uid, gid
    import getpass
    from pwd import getpwnam
    user = getpass.getuser()
    uid = getpwnam(user).pw_uid
    gid = getpwnam(user).pw_gid

    # get bootstrap directory
    import luda
    bootstrap_path = os.path.join(os.path.dirname(luda.__file__), "bootstrap")
    bootstrap_str = Volume(bootstrap_path, "/bootstrap", "ro").string

    include_home = True
    if include_home:
        home_str = ""
        home_path = os.path.expanduser("~")
        if home_path not in [v.host_path for v in volume]:
            home_str = Volume(home_path, "/home/{0}".format(user)).string

    # prefer nvidia-docker over docker
    exe = which("nvidia-docker") or "docker"
    nvargs = [exe, "run", "--rm", "-ti"] + [v.string for v in volume]

    work_str = " -v {work}:/work --workdir /work".format(work=work)
    entrypoint_str = " --entrypoint /bootstrap/init.sh" \
                     " --env HOST_USER_ID={uid}" \
                     " --env HOST_GROUP_ID={gid}" \
                     " --env HOST_USER={user}".format(**locals())

    cmd = " ".join(nvargs)
    cmd += bootstrap_str
    cmd += entrypoint_str
    cmd += home_str
    cmd += work_str
    if display:
        cmd += add_display()
    if dev:
        cmd += " --env DEVTOOLS=1"
    cmd += " " + " ".join(docker_args)
    click.echo(cmd)
    subprocess.call(cmd, shell=True)

if __name__ == "__main__":
    main()
