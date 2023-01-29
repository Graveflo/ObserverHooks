from typing import Any, Concatenate, ParamSpec, Protocol, Type, TypeVar, Callable, Generic, Self

T = TypeVar('T')
T_R = TypeVar('T_R')
P_M = ParamSpec('P_M')
P_F = ParamSpec('P_F')


class SomeMethodMessage:
    def __init__(self, arg1=0, arg2=1):
        self.arg1 = arg1
        self.arg2 = arg2

    def validate(self, instance: 'ClientCall'):
        self.arg1 = 34


def validate(instance, arg1=0, arg2=1):
    pass

class bmw(Generic[P_M, P_F, T]):
    def __init__(self, instance, func: Callable[..., T], message_t):
        self.__self__ = instance
        self.__func__ = func
        self.message_t = message_t

    def __call__(self, *args: P_F.args, **kwargs: P_M.kwargs) -> T:
        message = self.message_t(**kwargs)
        message.validate(self.__self__)
        return self.__func__(self.__self__, message, *args)


class Decor(Generic[P_M, P_F, T]):
    def __init__(self, message_t: Type, func: Callable[P_F, T]):
        self.message_t = message_t
        self.func = func

    def __get__(self, instance, owner) -> Callable[Concatenate[Callable[P_F, T], P_M], T]:
        return bmw(instance, self.func, self.message_t)

def talk(message_t: Callable[P_M, Any]):
    def wrapped(func: Callable[Concatenate[Any, Any, P_F], T]) -> Decor[P_M, P_F, T]:
        return Decor(message_t, func)
    return wrapped


class TalkValidator:
    def __init__(self, validation_func) -> None:
        self.func = validation_func


from typing import TypedDict, Unpack

def some_function(soemthing:int, otherthing:str, arg1: int = 0, arg2: str = 'hi'): pass

def wrap_thing(func: Callable[P_F, T]) -> Protocol[P_F]:
    return type('f', (object,), {})()


class Unf(Protocol):
    name:str
    age:int

def test(something: Protocol):
    pass

dd = wrap_thing(some_function)



class ClientCall:

    @talk(SomeMethodMessage)
    def some_method(self, clap: SomeMethodMessage, addition: str) -> int:
        print(addition)
        print(clap)
        return clap.arg1


def main():
    c = ClientCall()
    test_me = c.some_method()


if __name__ == '__main__':
    main()
