import requests
import json
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from random import randint

place_type = ["музеи", "достопримечательности", "галереи"]
keyboard_req_types = ["type", ]


def get_response(req):
    api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
    response = None
    search_api_server = "http://search-maps.yandex.ru/v1/"
    search_params ={
        "apikey": api_key,
        "text": req,
        "lang": "ru_RU",
        "type": "biz"
    }
    try:
        response = requests.get(search_api_server, params=search_params)
        if not response:
            return 'error'
        response = response.json()
        count = response["properties"]["ResponseMetaData"]["SearchResponse"]["found"]
        org_name = []
        if count >= 10:
            count = 10
        for i in range(count):
            organization = response["features"][i]
            org_name.append(organization["properties"]["CompanyMetaData"]["name"])
        return org_name
    except Exception:
        print('Error')

def vk_keyboard(req):
    global place_type
    keyboard = VkKeyboard(one_time=True)
    if req == 'type':
        for i in place_type:
            keyboard.add_button(i, color=VkKeyboardColor.POSITIVE)
    elif req == 'more':
        for i in req:
            keyboard.add_line()
            keyboard.add_button(i, color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()


def send_message(vk, user_id, text=None):
    vk.messages.send(
        user_id=user_id,
        message=text,
        random_id=randint(0, 2 ** 64)
    )



def main():
    token = ''
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            print('id{}: "{}"'.format(event.user_id, event.text))
            ask = event.text.lower().split()
            if "start" in ask:
                try:
                    text = 'Привет, ты хочешь узнать о достопримечательностях, музеях, галереях в городе? Напиши название твоего города и я посмотрю, куда ты сможешь сходить!'
                    send_message(vk, event.user_id, text)
                except Exception as exc:
                    print('Ошибка', exc)





if __name__ == '__main__':
    main()