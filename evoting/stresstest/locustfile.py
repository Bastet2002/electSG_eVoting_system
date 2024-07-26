import time
from locust import HttpUser, task, between

class QuickstartUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def home_page(self):
        self.client.get("/")
    
    @task(10)
    def view_singpass_login(self):
        self.client.get("/singpass_login")
    
    @task(1)
    def view_candidate_login(self):
        self.client.get("/login")

    # def on_start(self):
    #     self.client.post("/login", json={"username":"foo", "password":"bar"})