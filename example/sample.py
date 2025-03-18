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
