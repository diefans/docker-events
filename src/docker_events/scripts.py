import gevent
import gevent.monkey as gMonKey

gMonKey.patch_all()

import click
import inspect
from itertools import imap

import logging
import logging.config

import docker
import yaml

import simplejson as json

from . import event


LOG = logging.getLogger(__name__)


def setup_logging(logging_config, debug=False):
    """Setup logging config."""

    if logging_config is not None:
        logging.config.fileConfig(logging_config)

    else:
        logging.basicConfig(level=debug and logging.DEBUG or logging.ERROR)


def loop(sock, config=None):

    """Loops over all docker events and executes subscribed callbacks with an
    optional config value.

    :param config: a dictionary with external config values
    """

    if config is None:
        config = {}

    client = docker.Client(base_url=sock)

    # fake a running event for all running containers
    for container in client.containers():
        event_data = {
            'status': "running",
            'id': container['Id'],
            'from': container['Image'],
            'time': container['Created'],
        }

        LOG.debug("incomming event: %s", event_data)

        callbacks = event.filter_callbacks(client, event_data)

        # spawn all callbacks
        gevent.joinall([gevent.spawn(cb, event_data, config) for cb in callbacks])

    # listen for further events
    for raw_data in client.events():

        event_data = json.loads(raw_data)

        LOG.debug("incomming event: %s", event_data)

        callbacks = event.filter_callbacks(client, event_data)

        # spawn all callbacks
        gevent.joinall([gevent.spawn(cb, client, event_data, config) for cb in callbacks])


def join_configs(configs):

    """Join all config files into one config."""

    joined_config = {}

    for config in configs:
        joined_config.update(yaml.load(config))

    return joined_config


def load_modules(modules):
    for dotted_module in modules:
        try:
            __import__(dotted_module)

        except ImportError as e:
            LOG.error("Unable to import %s: %s", dotted_module, e)


def load_files(files):
    for py_file in files:
        LOG.debug("exec %s", py_file)
        execfile(py_file, globals(), locals())


def summarize_events():
    for ev in event.events:
        if ev.callbacks:
            LOG.info("subscribed to %s by %s", ev, ', '.join(imap(repr, ev.callbacks)))


@click.command()
@click.option("--sock", "-s",
              default="unix://var/run/docker.sock",
              help="the docker socket")
@click.option("configs", "--config", "-c",
              multiple=True,
              type=click.File("r"),
              help="a config yaml")
@click.option("modules", "--module", "-m",
              multiple=True,
              help="a python module to load")
@click.option("files", "--file", "-f",
              multiple=True,
              type=click.Path(exists=True),
              help="a python file to load")
@click.option("--log", "-l",
              type=click.Path(exists=True),
              help="logging config")
@click.option("--debug", is_flag=True,
              help="enable debug log level")
def cli(sock, configs, modules, files, log, debug):
    setup_logging(log, debug)

    config = join_configs(configs)

    # load python modules
    load_modules(modules)

    # load python files
    load_files(files)

    # summarize active events and callbacks
    summarize_events()

    LOG.debug("args: %s", locals())

    loop(sock=sock, config=config)
