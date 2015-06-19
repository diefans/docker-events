import docker


class DockerEvent(object):

    """A decorator, which registers a filter function to select a specific set
    of callbacks upon receiving the event."""

    # a singleton for all events
    events = []

    def __init__(self, func, *funcs):

        # we add a list of filter funcs that all have to resolve to True
        self.filters = (func, ) + funcs
        self._add_event(self)

        self.callbacks = []

        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    @classmethod
    def _add_event(cls, event):
        cls.events.append(event)

    def extend(self, func):
        """Creates a new Event."""
        print "event", func

        return self.__class__(func, *self.filters)

    def subscribe(self, func):
        """Register a callback which is called if the event gets triggered."""

        self.callbacks.append(func)

    def matches(self, event_data):
        """True if all filters are matching."""

        for f in self.filters:
            if not f(event_data):
                return False

        return True

    @classmethod
    def filter_events(cls, event_data):
        """Filter registered events and yield them."""

        for event in cls.events:
            # try event filters
            if event.matches(event_data):
                yield event

    @classmethod
    def filter_callbacks(cls, event_data):
        """Filter registered events and yield all of their callbacks."""

        for event in cls.filter_events(event_data):
            for cb in event.callbacks:
                yield cb


@DockerEvent
def docker_pull(event_data):
    return event_data.get('status') == 'pull'


@docker_pull.extend
def docker_pull_arango(event_data):
    return event_data.get('id').startswith("arango/")


def loop():
    client = docker.Client()

    for event_data in client.events():
        print event_data

