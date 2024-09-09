
import typing
T = typing.TypeVar('T')
A = typing.TypeVar('A')

class BaseAdaptor(object):

    __adaptorCls: None
    __modelCls: None

    def __init__(self, adaptorCls: typing.Type[A], modelCls: typing.Type[T]):
        self.__adaptorCls = adaptorCls
        self.__modelCls = modelCls        

    def translate(self, raw_dict) -> T:
        pass
        

