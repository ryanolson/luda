# -*- coding: utf-8 -*-
import os
import subprocess

import click
import docker

from j2docker import j2docker
from luda import which, Volume, add_display, parse_tuple
from utils import tempdir

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


APP_NAME = 'luda'

PathType = click.Path(exists=True, file_okay=True,
                      dir_okay=True, resolve_path=True)

def read_config():
    cfg = os.path.join(click.get_app_dir(APP_NAME), 'config.ini')
    parser = ConfigParser.RawConfigParser()
    parser.read([cfg])
    rv = {}
    for section in parser.sections():
        for key, value in parser.items(section):
            rv['%s.%s' % (section, key)] = value
    return rv

def get_template_path(template):
    template_path = os.path.join(click.get_app_dir(APP_NAME), 'templates', template, "Dockerfile")
    if not os.path.isfile(template_path):
        raise ValueError("{0}: {1} was not found.".format(template, template_path))
    return template_path

def generate_dockerfile_extension(base_image, template_name):
    template_path = get_template_path(template_name)
    with tempdir():
        with open("Dockerfile", "w") as output:
            output.write(j2docker.render(base_image, template_path))
        client = docker.from_env()
        tag = "luda/{0}:{1}".format(base_image.replace('/','-').replace(':', '-'), template_name)
        click.echo("Building image: {0} ...".format(tag))
        client.images.build(path=os.getcwd(), tag=tag)
    return tag


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
        return Volume.fromString(value)


@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.option("--work", default=None,
              help="Specifies a volume mount host_path:container_path; defaults to $PWD:/work. " +
                   "If None is passed, no /work or equivalent volume is mounted.")
@click.option("--home/--no-home", default=True, help="Flag to mount ~/ to /home/$USER in the container. Default: True")
@click.option("-v", "--volume", type=DockerVolumeType(), multiple=True,
              help="Mounts volumes. Functions identical to docker's native '-v' command")
@click.option('--display', is_flag=True,
              help="Sets up the environment to allow OpenGL contexts to be created")
@click.option('--docker', is_flag=True, help="Mounts the Docker socket inside the container")
@click.option('--dev', is_flag=True,
              help="Adds the DEVTOOLS environment variable. Forces 'apt update' and 'apt " +
                   "install -y --no-install-recommends sudo' to be run before launching the " +
                   "container")
@click.option('--rm', is_flag=True, help="Automatically remove the container when it exits (incompatible with -d)")
@click.option('-t', '--tty', is_flag=True, help="Allocate a pseudo-tty")
@click.option('-i', '--stdin', is_flag=True, help="Keep STDIN open even if not attached")
@click.option('-d', '--detach', is_flag=True,
              help="Detached mode: Run container in the background, print new container id")
@click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)
def main(docker_args, display, docker, dev, rm=None, detach=None, tty=None, stdin=None,
         work=None, home=None, volume=None):
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
    bootstrap_vol = Volume(bootstrap_path, "/bootstrap", "ro")

    # prefer nvidia-docker over docker
    exe = which("nvidia-docker") or "docker"
    args = ["run"]

    if rm:
        args.append("--rm")
    if detach:
        args.append("-d")
    if tty:
        args.append("-t")
    if stdin:
        args.append("-i")


    entrypoint_str = " --entrypoint /bootstrap/init.sh" \
                     " --env HOST_USER_ID={uid}" \
                     " --env HOST_GROUP_ID={gid}" \
                     " --env HOST_USER={user}"\
                     " --env HOST_GROUP={group}".format(**locals())
    args.append(bootstrap_vol.string)
    args.append(entrypoint_str)

    if home:
        home_vol = Volume("~", "/home/{0}".format(user))
        if home_vol.host_path not in [v.host_path for v in volume]:
            args.append(home_vol.string)

    work_vol = None
    if work is None:
        work_vol = Volume(os.getcwd(), "/work")
    elif work.lower() != "none":
        work_vol = Volume.fromString(work)
    if work_vol:
        args.append("{0} --workdir {1}".format(work_vol.string, work_vol.container_path))

    if display:
        args.append(add_display())

    nvargs = [exe] + [v.string for v in volume] + args

    image_and_args = ()
    docker_args_iter = iter(docker_args)

    # Remove pairs of arguments that start before the docker image
    for d_arg in docker_args_iter:
        if not image_and_args and d_arg.strip().startswith("-"):
            # skip the next two
            next(docker_args_iter, None)
            continue

        # otherwise, add it to the image and image args
        image_and_args += (d_arg,)

    # Get the docker command if no args were specified
    if len(image_and_args) == 1:
        ep_str = subprocess.Popen([exe, 'inspect', '-f "{{.Config.Entrypoint}}"', image_and_args[0]],
                                  stdout=subprocess.PIPE).stdout.read()

        # click.echo(ep_str)
        ep_str = parse_tuple(ep_str)

        # add the entry point if it exists
        if ep_str and len(ep_str) > 0:
            docker_args += (ep_str,)

        # koutputs an array of cmds
        curr_cmd = subprocess.Popen([exe, 'inspect', '-f "{{.Config.Cmd}}"', image_and_args[0]],
                                    stdout=subprocess.PIPE).stdout.read()
        # click.echo(curr_cmd)
        curr_cmd = parse_tuple(curr_cmd)

        if curr_cmd:
            docker_args += (curr_cmd,)

    docker_args = list(docker_args)

    if dev:
        image = generate_dockerfile_extension(image_and_args[0], "dev")
        docker_args[0] = image

    cmd = " ".join(nvargs + docker_args)
    click.echo(cmd)
    subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    main()
