# coding=utf-8
from __future__ import unicode_literals

from time import mktime
from datetime import datetime
from ...pipeline.pipes.base import BasePipe


class MetaPipe(BasePipe):

    def set_request(self, request):
        for node in request.values():
            node.meta['modified_at'] = self._utc_timestamp()

    def publish_request(self, request):
        for node in request.values():
            node.meta['published_at'] = self._utc_timestamp()

    def _utc_timestamp(self):
        return int(mktime(datetime.utcnow().timetuple()))
