from app.user.controllers.UserController import UserController
from utils.LambdaRequest import request

user = UserController()


def user_registration(event, context):
    return user.registration(request(event))
