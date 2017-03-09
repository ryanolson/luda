luda

ludicrously awesome [w]rapper for nvidia-docker


* Free software: MIT license
* Documentation: [coming shortly]

```
pip install git+https://github.com/ryanolson/luda.git
```

Note: On a Mac, you will need to install this somewhere else besides
`/usr/local/` because of Docker's restrictions on touching the host OS.

```
cd Projects
git clone https://github.com/ryanolson/luda.git
cd luda
pip install -e .
```


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

