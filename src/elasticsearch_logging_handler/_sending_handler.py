import sys
import threading
import traceback as tb
from datetime import datetime
from logging import Handler, LogRecord

import elasticsearch as es
import elasticsearch.helpers as es_helpers
import pytz


class ElasticSendingHandler(Handler):
    def __init__(
        self,
        level,
        es_client: es.Elasticsearch,
        index: str,
        flush_period: float = 1,
        batch_size: int = 1,
        timezone: str = "Asia/Ho_Chi_Minh",
    ) -> None:
        super().__init__(level=level)

        self._es_client = es_client
        self._index = index

        self._flush_period = flush_period
        self._batch_size = batch_size
        self._timezone = timezone

        self.__message_buffer = []
        self.__buffer_lock = threading.Lock()

        self.__timer: threading.Timer = None
        self.__schedule_flush()

    def __schedule_flush(self):
        """Start timer that one-time flushes message buffer."""

        if self.__timer is None:
            self.__timer = threading.Timer(self._flush_period, self.flush)
            self.__timer.setDaemon(True)
            self.__timer.start()

    def flush(self):
        """Send all messages from buffer to es.Elasticsearch."""

        if self.__timer is not None and self.__timer.is_alive():
            self.__timer.cancel()

        self.__timer = None

        if self.__message_buffer:
            try:
                with self.__buffer_lock:
                    actions, self.__message_buffer = self.__message_buffer, []

                es_helpers.bulk(self._es_client, actions, stats_only=True)
            except Exception:
                tb.print_exc(file=sys.stderr)

    def emit(self, record: LogRecord):
        """Add log message to the buffer. \n
        If the buffer is filled up, immedeately flush it."""

        action = self.__prepare_action(record)

        with self.__buffer_lock:
            self.__message_buffer.append(action)

        if len(self.__message_buffer) >= self._batch_size:
            self.flush()
        else:
            self.__schedule_flush()

    def __prepare_action(self, record: LogRecord):
        timestamp_dt: datetime = datetime.fromtimestamp(record.created)

        if self._timezone:
            tz_info = pytz.timezone(self._timezone)
            timestamp_dt: datetime = timestamp_dt.astimezone(tz_info)

        timestamp_iso = timestamp_dt.isoformat()

        message = record.msg

        action = {
            "_index": self._index,
            "_op_type": "index",
            "@timestamp": timestamp_iso,
            "level": record.levelname,
            "message": message,
            "extra": record.__dict__.get("extra", {}),
        }

        return action

    def close(self):
        self.flush()

        return super().close()
