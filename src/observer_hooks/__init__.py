from .observer_hooks import *
from .decorators import *
VERSION = "1.3.0"


class EventCapturer:
    def __init__(self, event: EventHandler | BoundEvent):
        self.captured_data = []
        self.event = event

    def slack(self, *args, **kwargs):
        if args:
            if kwargs:
                self.captured_data.append((args, kwargs))
            else:
                self.captured_data.append(args)
        else:
            if kwargs:
                self.captured_data.append(kwargs)
            else:
                self.captured_data.append(tuple())

    def __enter__(self):
        self.event.subscribe(self.slack)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.event.unsubscribe(self.slack)

    def __len__(self):
        return len(self.captured_data)

    def __str__(self):
        return f'EventCapture({self.event})'
