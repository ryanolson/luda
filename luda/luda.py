# -*- coding: utf-8 -*-
import os

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
    Create volume mappings for `docker`, `nvidia-docker` if present and the various components
    like the unitx socket for docker in the container to communicate back to the host.
    """
    docker_path = which("docker")
    nvdocker_path = which("nvidia-docker")
    # can i query docker for the location of the docker for the location of the
    # socket?
    # `docker info` will return "Docker Root Dir: /var/lib/docker"
    # check CoreOs project for detail on nvidia-docker socket

