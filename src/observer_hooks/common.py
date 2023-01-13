# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ ❧
"""


class AbortNotifyException(Exception):
    def __init__(self, return_value, *args, **kwargs):
        self.return_value = return_value
        super(AbortNotifyException, self).__init__(*args, **kwargs)
