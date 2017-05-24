# -*- coding: utf-8 -*-

import os
import subprocess
import click


from luda import which, Volume, add_display, parse_tuple

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
@click.option("--work", type=PathType, default=os.getcwd(),
              help="Specifies the work directory to use. This is mounted to /work in the container")

@click.option('--no_work_dir', is_flag=True,
              help="Prevents binding any volume to the containers /work directory. " + \
                   "This is necessary if the container already has a /work directory")

@click.option("-v", "--volume", type=DockerVolumeType(), multiple=True,
              help="Mounts volumes. Functions identical to docker's native '-v' command")

@click.option('--display', is_flag=True,
              help="Sets up the environment to allow OpenGL contexts to be created")

@click.option('--docker', is_flag=True)

@click.option('--dev', is_flag=True,
              help="Adds the DEVTOOLS environment variable. Forces 'apt update' and 'apt " + \
                   "install -y --no-install-recommends sudo' to be run before launching the" + \
                   " container")

@click.option('-d', '--docker_run_args', nargs=1, type=click.UNPROCESSED, default='--rm -ti',
              help="The run arguments for docker appended before the image name. Make sure to quote " + \
                   "the arguments, i.e. '-d -t'.")

@click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)

def main(docker_args, display, docker, dev, no_work_dir, docker_run_args=None, work=None, volume=None):

    """Console script for luda.

    docker_run_args - The run arguments for docker appended in the begining.
    Default "--rm -ti". Quote the arguments, i.e. "-d -t".

    docker_args - Remaining docker arguments appended at the end.
    """

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
    exe = which("nvidia-docker") or "docker"
    nvargs = [exe, 'run', docker_run_args] + [v.string for v in volume]

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
