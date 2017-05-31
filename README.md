# luda

ludicrously awesome [w]rapper for nvidia-docker


* Free software: MIT license
* Documentation: [coming shortly]

```
pip install luda
```

## Quickstart

```
luda nvidia/cuda:8.0-devel
```

todo: describe what luda is doing with the simpliest of commands

### Volumes

luda intercepts the `-v/--volume` option and provides convenience methods similar to
`docker-compose` in that relative paths are supported.  If no

```
# absolute path readonly
--volume /path/data:/data:ro

# relative path readonly
--volume /path/data:/data:ro

# relative path, no internal path --> mount internal at `/{{ basename(hostpath) }}`
# mounts $PWD/data --> /data inside the container
# --volume data

# same as above, but readonly
# --volume data::ro
```

### Abbreviations

You can set up abbreviations for commonly used URLs by including an `abbreviations` key in the yaml config file. By default,
luda includes the `nv:` which expands to `nvcr.io/nvidia/{0}`, where `{0}` is the remainding portion of the image name after
the abbreviation.

in `config.yml`
```
abbreviations:
  nv: nvcr.io/nvidia/{1}
```

Usage `nv:tensorflow:17.04` expands to `nvcr.io/nvidia/tensorflow:17.04`:
```
luda nv:tensorflow:17.04
```

### Displays

```
luda --with-display nvidia/cuda:8.0-devel
```

todo: show opengl containers

### Docker

```
luda --with-docker nvidia/cuda:8.0-devel
```

### Templates

Templates provide an easy way to extend container images with pre-defined content.
Assume I have the following `Dockerfile` defined in `~/.config/luda/templates/dev`.

```
RUN apt-get update && apt-get install -y --no-install-recommends \
        vim sudo python-dev python-pip && \
    rm -rf /var/lib/apt/lists/*

RUN pip install luda
```

The developer option `--dev` is a special case of `--template dev`.  Running the following commands performs a one-time
extensions of the `nvidia/cuda:8.0-devel` image with the `Dockerfile` above.  The new images generated will be
`luda/nvidia-cuda-8.0-devel:dev` or `luda/{{ base_image }}:{{ template }}` where `base_image` has all `/` and `:` replaced
with `-`.


```
luda --dev nvidia/cuda:8.0-devel
```

```
luda --template dev nvidia/cuda:8.0-devel
```

The first time this command is invoked `luda/nvidia-cuda-8.0-devel:dev` will be created.  Subsequent invocation will
either update the image if either the base image (`nvidia/cuda:8.0-devel`) or the template directory
(`~/.config/luda/templates/dev`) has detected changes.


## Features

* Opinionated wrapper for `docker`/`nvidia-docker` designed to provide
  Singularity-like functionality to Docker images.

* Best used for container images that run DL/HPC-like jobs, not suited
  for long-running daemons or services that require root.

* Volume mounts a /bootstrap volume and overrides the container image
  `ENTRYPOINT` to map the host USER, UID and GID [future work] into the
  container.  Current the docker commandline is echo'ed to the terminal on
  container startup.

* Automounts the current working directory on the host to `/work` inside
  the container.  `/work` becomes the current working directory inside the
  running container. `--work` can be used to specify an alternative default
  working directory for use inside the container; it will be mounted to `/work`.

* Automounts `$HOME` on the host to `/home/$USER` inside the container.
  `--home` option.k


## Acknowledgements

Thanks to [Deni Bertovic's
blog](https://denibertovic.com/posts/handling-permissions-with-docker-volumes/).
`luda` provides very similar functionality but does not require specially
crafted base images and wraps the details of the docker command-line.

The project contains a copy of [`su-exec`](https://github.com/ncopa/su-exec).
Copyright reproduced below.

```
The MIT License (MIT)

Copyright (c) 2015 ncopa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

