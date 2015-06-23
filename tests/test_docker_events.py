import pytest


@pytest.fixture
def FooEvent():
    """Just to have a clean singleton list."""

    from docker_events import event

    class FooEvent(event):
        events = []

    return FooEvent


def test_init(FooEvent):

    def foo():
        """foo doc"""
        pass

    foo_ = foo
    foo = FooEvent(foo)

    assert FooEvent.events == [foo]
    assert foo.__name__ == 'foo'
    assert foo.__doc__ == "foo doc"
    assert foo.filters == (foo_,)


def test_filter_chaining(FooEvent):

    def foo():
        pass

    foo_ = foo
    foo = FooEvent(foo)

    def bar():
        pass

    bar_ = bar
    bar = foo.extend(bar)

    assert FooEvent.events == [foo, bar]
    assert bar.filters == (bar_, foo_)


@pytest.fixture
def foo_event(FooEvent):
    @FooEvent
    def foo(client, event_data):
        return event_data > 0

    return foo


@pytest.fixture
def bar_event(foo_event):
    @foo_event.extend
    def bar(client, event_data):
        return event_data % 2 == 0

    return bar


@pytest.mark.parametrize("data, match", [
    (0, False),
    (1, True),
])
def test_matches_foo(data, match, foo_event):
    assert foo_event.matches(None, data) == match


@pytest.mark.parametrize("data, match", [
    (0, False),
    (1, False),
    (2, True),

])
def test_matches_bar(data, match, bar_event):
    assert bar_event.matches(None, data) == match


def test_filter(FooEvent, foo_event, bar_event):
    assert list(FooEvent.filter_events(None, 0)) == []
    assert list(FooEvent.filter_events(None, 1)) == [foo_event]
    assert list(FooEvent.filter_events(None, 2)) == [foo_event, bar_event]


@pytest.mark.parametrize("data, foo_t, bar_t", [
    (0, 0, 0),
    (1, 1, 0),
    (2, 1, 1),
    (3, 1, 0),
])
def test_callbacks(data, foo_t, bar_t, FooEvent, foo_event, bar_event):

    c = {
        'foo': 0,
        'bar': 0
    }

    @foo_event.subscribe
    def foo(client, event_data):
        c['foo'] += 1
        assert event_data > 0

    @bar_event.subscribe
    def bar(client, event_data):
        c['bar'] += 1
        assert event_data % 2 == 0

    for cb in FooEvent.filter_callbacks(None, data):
        cb(None, data)

    assert c['foo'] == foo_t
    assert c['bar'] == bar_t
