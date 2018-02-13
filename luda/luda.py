# -*- coding: utf-8 -*-
from __future__ import print_function
import os

import click
import docker

from j2docker import j2docker

from .config import get_template_path
from .utils import cd

class Volume(object):

    def __init__(self, host_path, container_path=None, readonly=None):

        host_path = os.path.expanduser(host_path)

        if os.path.exists(host_path):
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

    @classmethod
    def fromString(cls, string):
        return Volume(*string.split(":"))

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


def add_docker():
    """
    Create volume mappings for `docker`, `nvidia-docker` if present and the
    various components like the unitx socket for docker in the container to
    communicate back to the host.
    """
    pass
    # can i query docker for the location of the docker for the location of the
    # socket?
    # `docker info` will return "Docker Root Dir: /var/lib/docker"
    # check CoreOs project for detail on nvidia-docker socket


def add_display():
    """
    -v /tmp/.X11-unix:/tmp/.X11-unix \ # mount the X11 socket
    --env="DISPLAY"
    """
    try:
        vol = Volume("/tmp/.X11-unix", "/tmp/.X11-unix")
        return "--env=\"DISPLAY\""
    except:
        print("Warning: DISPLAY not passed thru")
        return ""

def parse_tuple(tuple_string):
    """
    strip any whitespace then outter characters.
    """
    return tuple_string.strip().strip("\"[]")


def expand_abbreviations(template, abbreviations):
    """Expand abbreviations in a template name.
    :param template: The project template name.
    :param abbreviations: Abbreviation definitions.
    """
    if template in abbreviations:
        return abbreviations[template]

    # Split on colon. If there is no colon, rest will be empty
    # and prefix will be the whole template
    prefix, sep, rest = template.partition(':')
    if prefix in abbreviations:
        return abbreviations[prefix].format(rest)

    return template

def generate_dockerfile_extension(base_image, template_name, config_path):
    """
    Extends the base_image with a named template.
    
    :param base_image: 
    :param template_name: 
    :return: name of created docker image (type=string)
    """
    template_path = get_template_path(template_name, config_path)
    template_file = os.path.join(template_path, "Dockerfile")
    dockerfile = ".Dockerfile.luda"

    def remove():
        if os.path.exists(dockerfile):
            os.remove(dockerfile)

    with cd(template_path, remove):
        with open(dockerfile, "w") as output:
            docker_str = j2docker.render(base_image, template_file).decode().strip()
            output.write(docker_str)
        client = docker.from_env()
        if base_image.startswith("luda/"):
            _, _, image_name = base_image.partition("luda/")
            image_name, _, tag = image_name.partition(":")
            image_name = "luda/{0}:{1}-{2}".format(image_name, tag, template_name)
        else:
            image_name = "luda/{0}:{1}".format(base_image.replace('/', '-').replace(':', '-'), template_name)
        click.echo("Building image: {0} ...".format(image_name))
        client.images.build(path=os.getcwd(), tag=image_name, dockerfile=dockerfile) # This line doesn't work with Python 3...
    return image_name
