class TempVoter:
    def __init__(self, username, district):
        self.username = username
        self.district = district
        self.is_authenticated = True

    def __str__(self):
        return self.username

    