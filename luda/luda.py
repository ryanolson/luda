# -*- coding: utf-8 -*-
import os


class Volume(object):

    def __init__(self, host_path, container_path=None, readonly=None):
        host_path = os.path.expanduser(host_path)
        if os.path.exists(host_path):
            host_path = os.path.abspath(host_path)
        else:
            raise ValueError("host path does not exist")

        container_path = container_path or os.path.join("/", os.path.basename(host_path))

        if isinstance(readonly, basestring):
            readonly = True if readonly.lower() == "ro" else False

        self.host_path = host_path
        self.container_path = container_path
        self.readonly = readonly

    @property
    def string(self):
        string = " --volume {host_path}:{container_path}"
        string += ":ro" if self.readonly else ""
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


class User(object):

    def __init__(self):
        import getpass
        from pwd import getpwnam
        import grp
        self._user = getpass.getuser()
        self._uid = getpwnam(self._user).pw_uid
        self._gid = getpwnam(self._user).pw_gid
        self._group = grp.getgrgid(self._gid).gr_name

    @property
    def user(self):
        return self._user

    @property
    def group(self):
        return self._group

    @property
    def groups(self):
        return None

    @property
    def uid(self):
        return self._uid

    @property
    def gid(self):
        return self._gid


def get_user_info():
    """
    
    :return: 
    """
    return

class LudaContext(object):

    def __init__(self):
        self._volumes = []

    def add_volume(self, host_path, container_path=None, readonly=None):
        self._volumes.append(Volume(host_path, container_path=container_path, readonly=readonly))

    def add_docker(self):
        socket = "/var/run/docker.sock"  # TODO use docker to find the .sock
        if os.path.exists(socket):
            self.add_volume(vol, "/var/run/docker.sock")
            # to add docker to the container, we can do one of two things:
            # 1) add the host's docker executable to the container
            # 2) extend the container and install docker
            # TODO - create the option for extending the container
            docker_path = which("docker")
            nvdocker_path = which("nvidia-docker")
            self.add_volume(docker_path, "/usr/bin/docker", readonly=True)
            if nvdocker_path:
                self.add_volume(nvdocker_path, "/usr/bin/nvidia-docker", readonly=True)
        else:
            raise ValueError("docker socket was not found")


    def generate_docker_command(self):
        pass

    def user_envs(self):
        """
        
        :return: 
        """
        " --env HOST_USER_ID={uid}" \
        " --env HOST_GROUP_ID={gid}" \
        " --env HOST_USER={user}" \
        " --env HOST_GROUP={group}".format(**locals())

def add_x11():
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
