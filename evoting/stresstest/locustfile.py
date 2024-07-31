import time
from locust import HttpUser, task, between
from locust.exception import StopUser
import random
import time

def get_voter_credentials():
    with open("./singpass_login.csv") as f:
        lines = f.readlines()
    return lines

def get_candidate_id():
    with open("./candidate_id.csv") as f:
        lines = f.readlines()
    data = {}
    for line in lines:
        parts = line.split(" ")
        id = int(parts[0])
        district = " ".join(parts[1:]).strip()
        if district in data:
            data[district].append(id)
        else:
            data[district] = [id]
    return data

def get_csrfmiddlewaretoken(response):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    csrf_token = soup.find("input", {"name":"csrfmiddlewaretoken"})
    if csrf_token:
        return csrf_token['value']
    return None

SINGPASS_CREDENTIALS = get_voter_credentials()
CANDIDATE_IN_DISTRICT = get_candidate_id()
district_num =len(CANDIDATE_IN_DISTRICT.keys())
# CHANGE STATUS TO POOLING DAY BEFORE ELECTION

# class GeneralUser(HttpUser):
#     wait_time = between(5, 10)

#     @task
#     def home_page(self):
#         self.client.get("/")
    
#     @task(3)
#     def view_announcements(self):
#         self.client.get("/announcements")
    
#     @task(5)
#     def view_districts(self):
#         self.client.get("/districts")

#     @task(10)
#     def view_district_ongoing(self):
#         self.client.get(f"/districts/{random.randint(1, district_num)}")


class SingpassUser(HttpUser):
    has_voted = False
    wait_time = between(10, 30)

    def get_csrf_token(self, url):
        return self.client.get(url).cookies['csrftoken']

    def on_start(self):
        self.client.base_url = "https://elect-sg.cookndrum.com"
        self.client.cookies.clear()
        self.client.headers.update({"X-Locust-Test":"true"})
        if SINGPASS_CREDENTIALS:
            parts = SINGPASS_CREDENTIALS.pop().split(" ") 
            self.singpass_id = parts[0]
            self.password = parts[1]
            self.district = " ".join(parts[2:]).strip()
            print(f'User {self.singpass_id} with password {self.password} in district {self.district} is starting')
            self.login()
        else:
            self.environment.runner.quit()
    
    def login(self):
        response = self.client.get("/singpass_login/")

        # print('Print the response from /singpass_login/')
        # print(response.text)

        # csrf_token = response.cookies['csrftoken']
        csrf_token = get_csrfmiddlewaretoken(response)
        # print(f'Initial CSRF token: {csrf_token} for {self.singpass_id}')

        header = {"X-CSRFToken":csrf_token,
                  "Referer": self.client.base_url + "/singpass_login/",
                  "Origin": self.client.base_url, "X-Locust-Test":"true", "Content-Type":"application/x-www-form-urlencoded"}
        data = {"singpass_id":self.singpass_id, "password":self.password,
                "csrfmiddlewaretoken":csrf_token}

        response = self.client.post("/singpass_login/",\
                                    data=data, headers=header, allow_redirects=True)

        if response.status_code == 200 and 'Voting Status' in response.text:
            print(f'Login success for user {self.singpass_id} in district {self.district}')
        else:
            print(f'Login failed for user {self.singpass_id} in district {self.district}')
            return
    
    @task(20)
    def voter_actions(self):
        if not self.has_voted:
            self.cast_vote()
        else:
            self.general_user_actions()

    def cast_vote(self):
        # self.client.cookies.update(self.session_cookies)
        response = self.client.get("/voter_home/ballot_paper/")

        if response.status_code == 200 and 'Ballot Paper' in response.text:
            print(f'Voter {self.singpass_id} in district {self.district} is viewing ballot paper')

            # time.sleep(random.randint(15, 60))

            csrf_token = get_csrfmiddlewaretoken(response)
            voting_csrf_token = csrf_token

            self.client.headers.update({"X-CSRFToken":voting_csrf_token})
            self.client.cookies.update({"csrftoken":voting_csrf_token})

            # # print(f'After update cookies: {self.client.cookies}')

            candidate_choice = random.choice(CANDIDATE_IN_DISTRICT[self.district])
            header = {"X-CSRFToken":voting_csrf_token, "Referer": self.client.base_url + "/voter_home/ballot_paper/",\
                    "Origin": self.client.base_url, "X-Locust-Test":"true"}
            data = {"csrfmiddlewaretoken":voting_csrf_token, "candidate": [candidate_choice]}

            # # print(f'Header in cast vote for {self.singpass_id}: {header}')
            # # print(f'Data in cast vote for {self.singpass_id}: {data}')

            response = self.client.post("/voter_home/ballot_paper/cast_vote/",\
                                        data=data, headers=header, allow_redirects=True)
        
            if response.status_code == 200 and 'Ballot Paper' in response.text:
                # if not voted, try again
                if not self.check_vote_status(response, candidate_choice):
                    response = self.client.post("/voter_home/ballot_paper/cast_vote/",\
                                                data=data, headers=header, allow_redirects=True)
                    if response.status_code == 200 and 'Ballot Paper' in response.text:
                        if not self.check_vote_status(response, candidate_choice):
                            print(f'Failed to vote for user {self.singpass_id} to vote for {candidate_choice} in district {self.district}')
                            return
        else:
            print(f'Failed to view ballot paper for user {self.singpass_id} in district {self.district}')
            return
        
        # need to logout to view result
        # raise StopUser()
    
    def check_vote_status(self, response, candidate_choice):
        response = self.client.get("/voter_home/")
        if response.status_code == 200 and "Haven't Voted" not in response.text:
            print(f'Voted for user {self.singpass_id} to vote for {candidate_choice} in district {self.district}')
            self.has_voted = True
            self.client.get("/logout") 
            return True
        return False
        
    
    def general_user_actions(self):
        action = random.choice(["home_page", "view_announcements", "view_districts", "view_district_ongoing"])
        if action == "home_page":
            self.client.get("/")
        elif action == "view_announcements":
            self.client.get("/announcements")
        elif action == "view_districts":
            self.client.get("/districts")
        elif action == "view_district_ongoing":
            self.client.get(f"/districts/{random.randint(1, district_num)}")
        
    
    # def view_live_result(self):
    #     response = self.client.get(f"/districts/{random.randint(1, district_num)}")
    #     if response.status_code == 200 and 'Ongoing Result' in response.text:
    #         print(f'User {self.singpass_id} in district {self.district} is viewing ongoing result')
    #     else:
    #         print(f'Failed to view ongoing result for user {self.singpass_id} in district {self.district}')
    #         # print(f"Status code: {response.status_code}")
    #         # print(f"Cookies: {dict(response.cookies)}")
    #         # print(f"Headers: {dict(response.headers)}")
    #         # print(f"Content: {response.text[:200]}...")
    #         return
        
    
    def on_stop(self):
        # self.client.get("/logout") # kill the session (we dont have auto kill session)
        self.client.cookies.clear()
