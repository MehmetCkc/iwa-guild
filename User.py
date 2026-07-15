from flask_login import UserMixin

class User(UserMixin):
    def __init__(self,id, email, password, name, surname, type, image):
        self.id = id
        self.email = email
        self.password = password
        self.name = name
        self.surname = surname
        self.type = type
        self.image = image