# -*- coding: utf-8 -*-

"""Global configuration handling."""

import collections
import copy
import io
import os

import click
import poyo


APP_NAME = 'luda'

BUILTIN_ABBREVIATIONS = {
    'nv': 'nvcr.io/nvidia/{0}',
}

DEFAULT_CONFIG = {
    'abbreviations': BUILTIN_ABBREVIATIONS,
}


def update(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d

def read_config(config_path):

    if not config_path:
        config_path = click.get_app_dir(APP_NAME)

    config_file = os.path.join(config_path, 'config.yml')
    config_dict = copy.copy(DEFAULT_CONFIG)
    if os.path.exists(config_file):
        with io.open(config_file, encoding='utf-8') as file_handle:
            yaml_dict = poyo.parse_string(file_handle.read())
        update(config_dict, yaml_dict)
    return config_dict


def get_template_path(template_name, config_path):

    if not config_path:
        config_path = click.get_app_dir(APP_NAME)

    template_path = os.path.join(config_path, 'templates', template_name)
    template_file = os.path.join(template_path, "Dockerfile")
    if not os.path.isdir(template_path):
        raise ValueError("{0} does not exist. Please create the template directory".format(template_path))
    if not os.path.isfile(template_file):
        raise ValueError("{0}: Dockerfile was not found in {1}.".format(template_name, template_path))
    return template_path
