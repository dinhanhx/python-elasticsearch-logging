import logging
import queue
import sys
import traceback as tb
from logging import NOTSET, Handler, LogRecord
from logging.handlers import QueueListener
from typing import Union

import elasticsearch as es

from ._queue_handler import ObjectQueueHandler
from ._sending_handler import ElasticSendingHandler


class ElasticHandler(Handler):
    def __init__(
        self,
        host: str,
        index: str,
        level=NOTSET,
        flush_period: float = 1,
        batch_size: int = 1,
        timezone: str = "Asia/Ho_Chi_Minh",
    ) -> None:
        """Elasticsearch Handler

        Parameters
        ----------
        host : str
            Url for Elasticsearch cluster.
            Currently, this handler support only basic authentication through providing user and password in the url.
            E.g. `https://user:password@my-cluster.es:9200`
        index : str
            Name of the Index to write in.
            This handler does not create index if there is no index with this name.
            E.g. `amazing-logs`
        level : _type_, optional
            This handler will only process messages with level larger than this parameter.
            by default NOTSET
        flush_period : float, optional
            Size of the buffer that stores logs before sending to Elasticsearch.
            If buffer is full, send batch immediately, without waiting for the flush_period,
            by default 1.0
        batch_size : int, optional
            Period during which handler will accumulate logs into batch before sending it ot the cluster,
            by default 1
        timezone : str, optional
            Timezone for which to transform @timestamp for the record,
            by default "Asia/Ho_Chi_Minh"
        """
        super().__init__(level)

        es_client = self._create_elastic_client(host)
        if es_client is None:
            # Disable emiting LogRecord to queue
            setattr(self, "emit", lambda *a, **kw: None)

            return
        else:
            self._es_client = es_client

        _queue = queue.Queue(maxsize=100000)

        # Object for writing logs to the queue.
        self._queue_handler = ObjectQueueHandler(_queue)

        # Object for reading logs from the queue.
        _elastic_listener = ElasticSendingHandler(
            level, es_client, index, flush_period=flush_period, batch_size=batch_size, timezone=timezone
        )
        self._queue_listener = QueueListener(_queue, _elastic_listener)
        self._queue_listener.start()

    def emit(self, record: LogRecord) -> None:
        """Write logs to the queue."""

        self._queue_handler.emit(record)

    def close(self) -> None:
        if hasattr(self, "_queue_listener"):
            self._queue_listener.stop()

        if hasattr(self, "_es_client"):
            self._es_client.close()

        return super().close()

    def _create_elastic_client(self, host) -> Union[es.Elasticsearch, None]:
        # Check all elastic configss are not None
        if host is None:
            return None

        try:
            es_client: es.Elasticsearch = es.Elasticsearch(hosts=[host])
            es_client.info()

            return es_client
        except es.exceptions.ConnectionError:
            logging.error("Can't connect to Elasticsearch host - {host}")

            return None
        except:
            tb.print_exc(file=sys.stderr)

            return None
