# -*- coding: utf-8 -*-
import os


class Volume(object):

    def __init__(self, host_path, container_path=None, readonly=None):

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
    -e DISPLAY=unix$DISPLAY
    """
    try:
        vol = Volume("/tmp/.X11-unix", "/tmp/.X11-unix")
        return "--env DISPLAY=unix{0} {1}".format(
            os.environ["DISPLAY"], vol.string)
    except:
        print "Warning: DISPLAY not passed thru"
        return ""
