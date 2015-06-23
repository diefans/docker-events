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

    skydns_config = config.get('skydns', {
        'domain': 'docker.local'
    })
    skydns_containers = config.get('skydns.containers', {})

    # find domain name for this container
    if skydns_config and container_name in skydns_containers:
        # use template
        sub_domain = skydns_containers[container_name].get('domain').format(**skydns_config)

    else:
        # join container_name with domain
        sub_domain = container_name

    domain = '.'.join((sub_domain.strip('.'), skydns_config.get('domain').strip('.')))

    domain_path = '/'.join(reversed(domain.split('.')))

    etcd_client.write('/skydns/{}'.format(domain_path), json.dumps({
        'host': container_ip
    }))
