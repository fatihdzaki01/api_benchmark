import time

from requests.exceptions import RequestException

from locust import HttpUser, task, between
from locust import stats as locust_stats
from locust import html as locust_html

locust_stats.PERCENTILES_TO_REPORT = [0.50, 0.90, 0.95]
locust_html.PERCENTILES_FOR_HTML_REPORT = [0.50, 0.90, 0.95]

CHUNK_SIZE = 65536


class FileUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def get_1kb(self):
        self._download("/files/1kb")

    @task(3)
    def get_10kb(self):
        self._download("/files/10kb")

    @task(2)
    def get_1mb(self):
        self._download("/files/1mb")

    @task(1)
    def get_10mb(self):
        self._download("/files/10mb")

    @task(1)
    def get_100mb(self):
        self._download("/files/100mb")

    def _download(self, path):
        start = time.perf_counter()
        with self.client.get(path, name=path, stream=True, catch_response=True) as response:
            try:
                if response.status_code != 200:
                    response.request_meta["response_time"] = (time.perf_counter() - start) * 1000
                    response.failure("HTTP %d" % response.status_code)
                    response.close()
                else:
                    total = 0
                    for chunk in response.iter_content(CHUNK_SIZE):
                        total += len(chunk)
                    response.request_meta["response_time"] = (time.perf_counter() - start) * 1000
                    response.request_meta["response_length"] = total
                    response.success()
            except RequestException as exc:
                response.request_meta["response_time"] = (time.perf_counter() - start) * 1000
                response.failure(exc)
                response.close()
