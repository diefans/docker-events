import docker
import logging


LOG = logging.getLogger(__package__)


class event(object):

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

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.__name__)

    @classmethod
    def _add_event(cls, event):
        cls.events.append(event)

    def extend(self, func):
        """Creates a new Event."""

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


@event
def pull(event_data):
    return event_data.get('status') == 'pull'


@event
def start(event_data):
    return event_data.get('status') == 'start'


@event
def create(event_data):
    return event_data.get('status') == 'create'


@event
def die(event_data):
    return event_data.get('status') == 'die'


@event
def stop(event_data):
    return event_data.get('status') == 'stop'


@event
def destroy(event_data):
    return event_data.get('status') == 'destroy'
