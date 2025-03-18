# elasticsearch-logging-handler

This is a minimalistic Elasticsearch logging handler for python. This handler uses only url as an authentication method. It is nonblocking, meaning any logging call e.g. logging.exception will not block calling thread. which is useful in the case of high logging load.

Thanks `https://github.com/Mulanir/python-elasticsearch-logging`

Note:
- This handler doesn't create index in elasticsearch if there is not one.
- This library doesn't come with an elasticsearch server or any script to start one.

## Installation

```
gh clone dinhanhx/python-elasticsearch-logging
cd elasticsearch_logging_handler/
pip install -e .
```

## Usage

```ini
ELASTIC_HOST=localhost:8801
ELASTIC_USERNAME=elastic 
ELASTIC_PASSWORD=empty
```

```python
import logging
import os

from dotenv import load_dotenv

from elasticsearch_logging_handler import ElasticHandler

load_dotenv()

user = os.getenv("ELASTIC_USERNAME")
password = os.getenv("ELASTIC_PASSWORD")
host = os.getenv("ELASTIC_HOST")
url = f"http://{user}:{password}@{host}"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

elastic_handler = ElasticHandler(url, "test-index", level=logging.INFO)
logger.addHandler(elastic_handler)

logger.info(msg=__name__, extra={"test": "test"})
```