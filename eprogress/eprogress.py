"""
This is originally a package called eprogress which can be installed by 'pip install eprogress'.
However there are too many bugs in it that my monkey patches almost cover the whole code.
So I forked it here for the convenience of my repairing.

The original package is under Apache Licence 2.0. For more detail see https://github.com/homgwu/eprogress.

Harrisson Chen<chenhao11@xioami.com> @ 09/13/17
"""

import abc
import re
import sys
import threading

CLEAR_TO_END = "\033[K"
UP_ONE_LINE = "\033[1A"


class ProgressBar(object, metaclass=abc.ABCMeta):
    def __init__(self, width=25, title=''):
        self.width = width
        self.title = ProgressBar.filter_str(title)
        self._lock = threading.Lock()

    @property
    def lock(self):
        return self._lock

    @abc.abstractmethod
    def update(self, progress=0):
        pass

    @staticmethod
    def filter_str(pending_str):
        """去掉字符串中的\r、\t、\n"""
        return re.sub(pattern=r'\r|\t|\n', repl='', string=pending_str)


class CircleProgress(ProgressBar):
    def __init__(self, width=10, title=''):
        """
         @param width : 进度条展示的长度
         @param title : 进度条前面展示的文字
        """
        super(CircleProgress, self).__init__(width=width, title=title)
        self._current_char = ''
        self._status = 0

    def update(self, progress=0):
        """
        @param progress : 当前进度值,非0则更新符号
        """
        with self.lock:
            if progress > 0:
                self._status = 1
            elif progress < 0:
                self._status = 0
            if self._status > 0:
                self._get_next_circle_char()
            sys.stdout.write('\r' + CLEAR_TO_END)
            sys.stdout.write("\r%s:[%s]" % (self.title, self._current_char))
            # sys.stdout.flush()

    def _get_next_circle_char(self):
        if self._current_char == '':
            self._current_char = '-'
        elif self._current_char == '-':
            self._current_char = '\\'
        elif self._current_char == '\\':
            self._current_char = '|'
        elif self._current_char == '|':
            self._current_char = '/'
        elif self._current_char == '/':
            self._current_char = '-'
        return self._current_char


class LineProgress(ProgressBar):
    def __init__(self, total=100, symbol='#', width=25, title='', is_2charswide=False):
        """
         @param total : 进度总数
         @param symbol : 进度条符号
         @param width : 进度条展示的长度
         @param title : 进度条前面展示的文字
         @param is_2charswide : 占位符是否2字符宽，适应Windows环境下某些占位符2字符宽的显示问题
        """
        super(LineProgress, self).__init__(width=width, title=title)
        self.total = total
        self.symbol = symbol
        self._current_progress = 0
        self.platform_adjustment = 2 if is_2charswide else 1

    def update(self, progress=0):
        """
        @param progress : 当前进度值
        """
        with self.lock:
            if progress > 0:
                self._current_progress = progress
            sys.stdout.write('\r' + CLEAR_TO_END)
            hashes = self.symbol * int(self._current_progress / self.total * self.width)
            spaces = ' ' * (self.width - len(hashes)) * self.platform_adjustment
            sys.stdout.write("\r%s:[%s] %d%%" % (self.title, hashes + spaces, int(self._current_progress / self.total * 100)))
            # sys.stdout.flush()


class MultiProgressManager(object):
    def __new__(cls, *args, **kwargs):
        """单例"""
        if not hasattr(cls, '_instance'):
            cls._instance = super(MultiProgressManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self._progress_dict = {}
        self._lock = threading.Lock()

    def put(self, key, progress_bar):
        with self._lock:
            if key and progress_bar:
                self._progress_dict[key] = progress_bar
                progress_bar.index = len(self._progress_dict) - 1

    def clear(self):
        with self._lock:
            self._progress_dict.clear()

    def update(self, key, progress):
        """
        @param key : 待更新的进度条标识
        @param progress : 当前进度值
        """
        with self._lock:
            if not key:
                return
            delta_line = len(self._progress_dict)
            sys.stdout.write(UP_ONE_LINE * delta_line if delta_line > 0 else '')
            bars = list(self._progress_dict.items())
            bars.sort(key=lambda x: x[1].index)
            for inner_key, bar in bars:
                if inner_key == key:
                    bar.update(progress)
                else:
                    bar.update(0)
                sys.stdout.write('\n')
