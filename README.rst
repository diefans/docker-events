docker-events
=============


objective
---------

* have a CLI to start a process which runs abitrary code on docker events
* be able to provide a way to change behavior of and provide data to event subscribers
* load subscribers by module or file
* events may be extended


install
-------

.. code-block:: shell

    # pip install docker-events


usage
-----

.. code-block:: shell

    # docker-events --help
    Usage: docker-events [OPTIONS]

    Options:
      -s, --sock TEXT        the docker socket
      -c, --config FILENAME  a config yaml
      -m, --module TEXT      a python module to load
      -f, --file PATH        a python file to load
      -l, --log PATH         logging config
      --debug                enable debug log level
      --help                 Show this message and exit.

    # create a config for skydns
    # cat > skydns-config.yaml << EOF
    ---

    skydns:
      domain: foo

    skydns.containers:
      redis:
        domain: myredis.{domain}
    EOF

   # run skydns subscriber on start events
   # docker-events -c skydns-config.yaml -m docker_events.tools.skydns



API
---

There are some predefined events: `start`, `stop`, `create`, `die`, `destroy`, `pull`

You may write your own events like this:

.. code-block:: python

    @event
    def pull(client, event_data):
        return event_data.get('status') == 'pull'


Events may be extended by other events:

.. code-block:: python

   @docker_events.pull.extend
   def pull_something(client, event_data):
       return event_data['id'].startswith("foobar")



For example if you want to use skydns, you may want to put the following code into a file or module and load it via `-m` or `-f` option:

.. code-block:: python

    """
    setup skydns records for containers
    """

    import docker_events
    import etcd
    import simplejson as json


    etcd_client = etcd.Client()


    @docker_events.start.subscribe
    def set_skydns_record(client, docker_event, config):
        # get ip of container
        container = client.inspect_container(docker_event['id'])

        container_name = container['Name'].strip("/")
        container_ip = container['NetworkSettings']['IPAddress']

        skydns_config = config.get('skydns', {})
        skydns_containers = config.get('skydns.containers', {
            'domain': 'docker.local'
        })

        # find domain name for this container
        if skydns_config and container_name in skydns_containers:
            # use template
            domain = skydns_containers[container_name].get('domain').format(**skydns_config)

        else:
            # join container_name with domain
            domain = '.'.join((container_name, skydns_config.get('domain')))

        domain_path = '/'.join(reversed(domain.split('.')))


        etcd_client.write('/skydns/local/skydns/{}'.format(domain_path), json.dumps({
            'host': container_ip
        }))

