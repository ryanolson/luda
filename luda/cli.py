# -*- coding: utf-8 -*-

import click
import os
import subprocess

from luda import which, Volume, add_display

PathType = click.Path(exists=True, file_okay=True,
                      dir_okay=True, resolve_path=True)


def exclusive(ctx_params, exclusive_params, error_message):
    """
    https://gist.github.com/thebopshoobop/51c4b6dce31017e797699030e3975dbf
    
    :param ctx_params: 
    :param exclusive_params: 
    :param error_message: 
    :return: 
    """
    if sum([1 if ctx_params[p] else 0 for p in exclusive_params]) > 1:
        raise click.UsageError(error_message)

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
@click.option('--rm', is_flag=True)
@click.option('-t', '--tty', is_flag=True)
@click.option('-i', '--stdin', is_flag=True)
@click.option('-d', '--detach', is_flag=True)
@click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)
def main(docker_args, display, docker, dev, rm=None, detach=None, tty=None, stdin=None, work=None,
         volume=None):
    """Console script for luda.

    docker_run_args - The run arguments for docker appended in the begining.
    Default "--rm -ti". Quote the arguments, i.e. "-d -t".

    docker_args - Remaining docker arguments appended at the end.
    """
    exclusive(click.get_current_context().params, ['detach', 'rm'], 'd and rm are mutually exclusive')

    # if no run options are given, set defaults
    if not (rm and detach and tty and stdin):
        rm = True
        tty = True
        stdin = True

    # get some data about the user: name, uid, gid
    import getpass
    from pwd import getpwnam
    import grp
    user = getpass.getuser()
    uid = getpwnam(user).pw_uid
    gid = getpwnam(user).pw_gid
    group = grp.getgrgid(gid).gr_name

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
    exe = [which("nvidia-docker") or "docker"]
    exe.append(("run"))

    if rm:
        exe.append("--rm")
    if detach:
        exe.append("-d")
    if tty:
        exe.append("-t")
    if stdin:
        exe.append("-i")

    nvargs = exe + [v.string for v in volume]

    work_str = " -v {work}:/work --workdir /work".format(work=work)
    entrypoint_str = " --entrypoint /bootstrap/init.sh" \
                     " --env HOST_USER_ID={uid}" \
                     " --env HOST_GROUP_ID={gid}" \
                     " --env HOST_USER={user}"\
                     " --env HOST_GROUP={group}".format(**locals())

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

