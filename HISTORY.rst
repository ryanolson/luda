=======
History
=======

0.1.0 (2017-03-07)
------------------

* First release on PyPI.

0.4.0 (2017-06-01)
------------------

* Added configurable abbreviations to simply long image names
* Added templates to extend images from reusable templated Dockerfiles
* Added entrypoint and command inspection on the base_image to ensure the correct scripts/commands
  executed on container launch
* Removed --docker_run_args and replaced with luda managed `--rm`, `-d`, `-t`, `-i` options which map
  directly to the docker equivalents
* Improved landing page documentation (still more needs to be done)
