import numpy as np
from eq_base_api import *

class NumericSeries(list):
    def __init__(self, rawList=[], isOpenLog=True):
        super().__init__(rawList)
        self._curBarIndex = -1
        self._isOpenLog = isOpenLog

    def __setitem__(self, key, value):
        length = super().__len__()
        curBarIndex = CurrentBar()

        if length == 0:
            super().append(value)
            self._curBarIndex = curBarIndex
        elif 0<=key<length-1 or -length<=key<-1:
            super().__setitem__(key, value)
        elif key==-1 or key==length-1:
            if self._curBarIndex == curBarIndex:  # curBarIndex是一样的
                super().__setitem__(key, value)
            elif self._curBarIndex+1 == curBarIndex:
                super().append(value)
                self._curBarIndex = curBarIndex
            elif self._isOpenLog:
                LogInfo(f"无效的参数, 当前self._curBarIndex = {self._curBarIndex}, currentBarIndex={curBarIndex}")
        elif self._isOpenLog:
            LogInfo(f"无效的参数,{key} {value}")

    #
    def __getitem__(self, item):
        if isinstance(item, slice):
            return super().__getitem__(item)
        
        length = len(self)
        if length == 0:
            return np.nan
        elif 0<=item<length or -length<=item<=-1:
            return super().__getitem__(item)
        elif item<0 and item<-length:
            if self._isOpenLog:
                LogInfo(f"无效的参数{item}, 实际返回下标{-length}")
            return super().__getitem__(-length)
        elif item>0 and item>length-1:
            if self._isOpenLog:
                LogInfo(f"无效的参数{item}, 实际返回下标{length-1}")
            return super().__getitem__(length-1)

    def __iter__(self):
        return super().__iter__()

    def append(self, value):
        self[-1] = value

    def __len__(self):
        return super().__len__()

    def __add__(self, other):
        if len(self) != len(other):
            if self._isOpenLog:
                LogInfo(f"长度不一样,{len(self)}, {len(other)}")
            return self
        result = [a+b for a, b in zip(self, other)]
        resultObj = self.__class__(result, self._isOpenLog)
        return resultObj

    def __sub__(self, other):
        pass

    def __mul__(self, other):
        pass

    def __truediv__(self, other):
        pass

    def __floordiv__(self, other):
        pass

    def __imod__(self, other):
        pass

    def __isub__(self, other):
        pass

    def __imul__(self, other):
        pass

    def __itruediv__(self, other):
        pass

    def __ifloordiv__(self, other):
        pass

    def __imod__(self, other):
        pass

    def __ipow__(self, other):
        pass

    def __pow__(self, other):
        pass

    def __abs__(self):
        pass

    def __repr__(self):
        pass

    def __contains__(self, item):
        pass

    def __and__(self, other):
        pass

    def __or__(self, other):
        pass

    def __xor__(self, other):
        pass

    def __lshift__(self, other):
        pass

    def __rshift__(self, other):
        pass

    def __neg__(self):
        pass

    def __pos__(self):
        pass

    def __invert__(self):
        pass
    
    # 调试函数__repr__和__str__
    def __repr__(self):
        return f"Meta Class: {self.__class__}:\nClass Member:\n\tsuper() = {list(super().__iter__())}\n\tself._isOpenLog = {self._isOpenLog}\n\tself._curBarIndex = {self._curBarIndex}"
    
    def __str__(self):
        return self.__repr__()
