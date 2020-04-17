import requests
import json
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from random import randint

place_type = ["музеи", "достопримечательности", "галереи"]
keyboard_req_types = ["type", "city"]


def get_response(req):
    api_key = ""
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
    except Exception as exc:
        print('Error', exc)


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


def create_empty_keyboard():
    keyboard = vk_api.keyboard.VkKeyboard.get_empty_keyboard()
    return keyboard


def send_message(vk, user_id, text=None, keyboard=create_empty_keyboard()):
    vk.messages.send(
        user_id=user_id,
        message=text,
        random_id=randint(0, 2 ** 64),
        keyboard=keyboard
    )


def add_users_data(id, status):
    with open('users.txt', 'a') as f:
        f.write('{} {}\n'.format(id, status))


def check_user():
    users_dict = {}
    with open('users.txt', 'r') as f:
        users = f.readlines()
    for i in range(len(users)):
        users[i] = users[i].split()
    for i in users:
        users_dict[i[0]] = i[1]
    return users_dict


def change_status(id, status):
    users = check_user()
    for i in users:
        if i == id:
            users[i] = status
    with open("users.txt", "w") as f:
        for i in users:
            f.write('{} {}\n'. format(i, users[i]))


print(check_user())


def main():
    token = ''
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            print('id{}: "{}"'.format(event.user_id, event.text))
            ask = event.text.lower().split()
            keyboard = vk_keyboard("type")
            empty_keyboard = create_empty_keyboard()
            users = check_user()
            if "привет" in ask:
                try:
                    send_message(vk, event.user_id, "Привет!", keyboard)
                    if event.user_id not in check_user():
                        add_users_data(event.user_id, "type")
                    if event.user_id in check_user():
                        change_status(event.user_id, "type")
                except Exception as exc:
                    print("Ошибка: ", exc)
            elif "достопримечательности" in ask:
                try:
                    send_message(vk, event.user_id, "Напиши название города, достопримечательности которого ты бы хотел посмотреть.")
                    if event.user_id not in check_user():
                        add_users_data(event.user_id, "достопримечательности")
                    if event.user_id in check_user():
                        change_status(event.user_id, "достопримечательности")
                except Exception as exc:
                    print("Ошибка: ", exc)
            elif "музеи" in ask:
                try:
                    send_message(vk, event.user_id, "Напиши название города, музеи которого ты бы хотел посмотреть.")
                    if event.user_id not in check_user():
                        add_users_data(event.user_id, "музеи")
                    if event.user_id in check_user():
                        change_status(event.user_id, "музеи")
                except Exception as exc:
                    print("Ошибка: ", exc)
            elif "галереи" in ask:
                try:
                    send_message(vk, event.user_id, "Напиши название города, галереи которого ты бы хотел посмотреть.")
                    if event.user_id not in check_user():
                        add_users_data(event.user_id, "галереи")
                    if event.user_id in check_user():
                        change_status(event.user_id, "галереи")
                except Exception as exc:
                    print("Ошибка: ", exc)
            elif (str(event.user_id) in users) and (users[str(event.user_id)] == "достопримечательности" or "музеи" or "галереи"):
                orgs = get_response(users[str(event.user_id)] + ask[0])
                print(orgs)
                text = ''
                for i in range(len(orgs)):
                    text += '{}. {}\n'.format(i + 1, orgs[i])
                try:
                    send_message(vk, event.user_id, text, keyboard)
                    if event.user_id in check_user():
                        change_status(event.user_id, "type")
                except Exception as exc:
                    print("Ошибка: ", exc)


if __name__ == '__main__':
    main()