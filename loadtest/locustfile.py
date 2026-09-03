import random
from locust import HttpUser, task, between


class FileUser(HttpUser):
    wait_time = between(0.1, 0.5)
    sizes = ["1kb", "10kb", "1mb", "10mb", "100mb"]

    @task(3)
    def get_1kb(self):
        self.client.get("/files/1kb", name="/files/1kb")

    @task(3)
    def get_10kb(self):
        self.client.get("/files/10kb", name="/files/10kb")

    @task(2)
    def get_1mb(self):
        self.client.get("/files/1mb", name="/files/1mb")

    @task(1)
    def get_10mb(self):
        self.client.get("/files/10mb", name="/files/10mb")

    @task(1)
    def get_100mb(self):
        self.client.get("/files/100mb", name="/files/100mb")

    @task(5)
    def health_check(self):
        self.client.get("/health", name="/health")
