# -*- coding: utf-8 -*-

import click
import collections
import os
import subprocess

PathType = click.Path(exists=True, file_okay=False,
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


def which(program):
    """
    Finds an executable in the system PATH.
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


class Volume(object):

    def __init__(self, host_path, container_path=None, readonly=None):
       
        if os.path.isdir(host_path):
            host_path = os.path.abspath(host_path)
        else:
            raise ValueError("host path does not exist")

        if not container_path:
            container_path = os.path.join("/", os.path.basename(host_path))

        readonly = ":ro" if readonly and readonly.lower() == "ro" else ""

        self.host_path = host_path
        self.container_path = container_path
        self.readonly = readonly

    @property
    def string(self):
        string = " -v {host_path}:{container_path}{readonly}"
        return string.format(**vars(self))


class DockerVolumeType(click.ParamType):
    name = 'volume'

    def convert(self, value, param, ctx):
        return Volume(*value.split(":"))


@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.option("-v", "--volume", type=DockerVolumeType(), multiple=True)
@click.option("--work", type=PathType, default=os.getcwd())
@click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)
def main(docker_args, work=None, volume=None):
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
    bootstrap_str = Volume(bootstrap_path, "/bootstrap").string

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
    cmd += " " + " ".join(docker_args)
    click.echo(cmd)
    subprocess.call(cmd, shell=True)

if __name__ == "__main__":
    main()
