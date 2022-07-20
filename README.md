# observer_hooks
A quick & dirty, but flexable way to attach side effects to functions and methods.
Intended to accomplish something similar to the "observer pattern" in simple context.

For methods, an instance member to hold weak references to functions and methods is automatically created. By default
the instance member is the same name as the method with an underscore prepended. This can be changed with the event_name
argument.

Side effects can be chained normally.

## Usage

Attach a side effect to a function:
```python
from observer_hooks import notify

@notify()
def some_function(param):
    return f"param: {param}"


def side_effect(param):
    print(param)


some_function.subscribe(side_effect)
assert some_function(1) == 'param: 1'
```

Attach a side effect to a method:
```python
from observer_hooks import notify

class A:
    @notify()
    def notify_some_action(self):
        pass

class B:
    def __init__(self, a:A):
        self.a = a
        a.notify_some_action.subscribe(self.a_some_action)
    
    def a_some_action(self):
        print('received')

b = B(A())
b.a.notify_some_action()
```

Example with __slots__:
```python
from observer_hooks import notify

class A:
    __slots__ = '_notify_some_action',
    
    @notify()
    def notify_some_action(self):
        pass

def a_some_action():
    print('received')

a = A()
a.notify_some_action.subscribe(a_some_action)
a.notify_some_action()
```

Block certain side effects from firing:
```python
from observer_hooks import notify, BlockSideEffects

class A:
    __slots__ = '_notify_some_action',

    @notify()
    def notify_some_action(self):
        pass

def a_some_action():
    print('blocked')

def a_some_action2():
    print('not blocked')

a = A()
a.notify_some_action.subscribe(a_some_action)
a.notify_some_action.subscribe(a_some_action2)
with BlockSideEffects(a.notify_some_action, only=(a_some_action,)):
    a.notify_some_action()
```


# Future plans

- Implement access to the originating functions return value
  - Either a member of the object that replaces the function for non-thread safe applications or a special parameter
- Implement access to notifying class to the notified functions similar to above