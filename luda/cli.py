# -*- coding: utf-8 -*-

import os
import subprocess
import click


from luda import which, Volume, add_display, parse_tuple

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
@click.option("--work", type=PathType, default=os.getcwd(),
              help="Specifies the work directory to use. This is mounted to /work in the container")
@click.option('--no_work_dir', is_flag=True,
              help="Prevents binding any volume to the containers /work directory. " + \
                   "This is necessary if the container already has a /work directory")
@click.option("-v", "--volume", type=DockerVolumeType(), multiple=True,
              help="Mounts volumes. Functions identical to docker's native '-v' command")
@click.option('--display', is_flag=True,
              help="Sets up the environment to allow OpenGL contexts to be created")
@click.option('--docker', is_flag=True, help="Mounts the Docker socket inside the container")
@click.option('--dev', is_flag=True,
              help="Adds the DEVTOOLS environment variable. Forces 'apt update' and 'apt " + \
                   "install -y --no-install-recommends sudo' to be run before launching the" + \
                   " container")
@click.option('--rm', is_flag=True, help="Automatically remove the container when it exits (incompatible with -d)")
@click.option('-t', '--tty', is_flag=True, help="Allocate a pseudo-tty")
@click.option('-i', '--stdin', is_flag=True, help="Keep STDIN open even if not attached")
@click.option('-d', '--detach', is_flag=True, help="Detached mode: Run container in the background, print new container id")
@click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)
def main(docker_args, display, docker, dev, rm=None, detach=None, tty=None, stdin=None, work=None,volume=None):
    """Console script for luda.

    For best results, use a `--` before the image name to ensure all arguments after the image are ignored by luda.
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

    image_and_args = ()

    docker_args_iter = iter(docker_args)

    #Remove pairs of arguments that start before the docker image
    for d_arg in docker_args_iter:
        if not image_and_args and d_arg.strip().startswith("-"):
            #skip the next two
            next(docker_args_iter, None)
            continue

        #otherwise, add it to the image and image args
        image_and_args += (d_arg,)

    #Get the docker command if no args were specified
    if len(image_and_args) == 1:
        ep_str = subprocess.Popen([exe, 'inspect', '-f "{{.Config.Entrypoint}}"', image_and_args[0]],
                                  stdout=subprocess.PIPE).stdout.read()

        #click.echo(ep_str)
        ep_str = parse_tuple(ep_str)

        #add the entry point if it exists
        if ep_str and len(ep_str) > 0:
            docker_args += (ep_str,)

        #outputs an array of cmds
        curr_cmd = subprocess.Popen([exe, 'inspect', '-f "{{.Config.Cmd}}"', image_and_args[0]],
                                    stdout=subprocess.PIPE).stdout.read()
        #click.echo(curr_cmd)
        curr_cmd = parse_tuple(curr_cmd)

        if curr_cmd:
            docker_args += (curr_cmd,)

    cmd = " ".join(nvargs) + " "
    cmd += bootstrap_str + " "
    cmd += entrypoint_str + " "
    cmd += home_str + " "
    if not no_work_dir:
        cmd += work_str + " "
    if display:
        cmd += add_display() + " "
    if dev:
        cmd += " --env DEVTOOLS=1" + " "
    cmd += " " + " ".join(docker_args)
    click.echo(cmd)
    subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    main()
