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

The HardRefEventHandler will hold non-weak references to lambda and partial functions
```python
from observer_hooks import notify, HardRefEventHandler

@notify(handler_t=HardRefEventHandler)
def notify_some_action():
    return 'return value'

def some_action():
    print('Hi')

def scope():
    notify_some_action.subscribe(lambda: some_action())

scope()
print(notify_some_action())
```

The "pass_ref" parameter will pass the "self" reference to side-effect functions and the switch_event_handler method on descriptors will switch the event handler type
```python
from observer_hooks import notify, HardRefEventHandler
class SomeClass:
    @notify(pass_ref=True)
    def method(self):
        pass

s = SomeClass()

def method(other):
    assert other is s

s.method.switch_event_handler(HardRefEventHandler())
s.method.subscribe(method)
s.method()
```

Inherit or copy parameters from a superclasses descriptor with 'notify_copy_super'

```python
from observer_hooks import notify, notify_copy_super


class A:
    @notify(pass_ref=True, no_origin=True, auto_fire=False)
    def method(self):
        print('this wont print')


class B(A):
    pass


class C(B):
    @notify_copy_super(auto_fire=True)
    def method(self):
        print('neither will this')


def side_effect(x):
    print('hi', x)


c = C()
c.method.subscribe(side_effect)
c.method()
```


Notes:
- The parameter "auto_fire" will disable all side effects and instead the .emit() function can be used to manually trigger the side effects
- Redefined methods in child classes also need the decorator and will override behavior to the specifications of the new decorator
- Inherited methods will only fire once even if they are re-defined and super is called
- Inherited methods do not need to be re-defined

# Future plans

- Implement access to the originating functions return value
  - Either a member of the object that replaces the function for non-thread safe applications or a special parameter
