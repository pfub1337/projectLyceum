import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import wikipedia
from random import randint
import sqlite3

place_type = ["музеи", "достопримечательности", "галереи"]


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
    except Exception as exc:
        print('Error', exc)


def vk_keyboard(req, req_list=None):
    if req_list is None:
        req_list = []
    global place_type
    keyboard = VkKeyboard(one_time=True)
    if req == 'type':
        for i in place_type:
            keyboard.add_button(i, color=VkKeyboardColor.POSITIVE)
    elif req == 'more':
        for i in range(0, len(req_list), 2):
            keyboard.add_button(req_list[i], color=VkKeyboardColor.POSITIVE)
            keyboard.add_button(req_list[i + 1], color=VkKeyboardColor.POSITIVE)
            keyboard.add_line()
        if len(req_list) % 2 == 1:
            keyboard.add_button(req_list[-1], color=VkKeyboardColor.POSITIVE)
            keyboard.add_line()
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
    con = sqlite3.connect("users.db")
    cur = con.cursor()
    cur.execute("INSERT INTO Users VALUES(?, ?)", (id, status))
    con.commit()
    con.close()


def check_user():
    con = sqlite3.connect("users.db")
    cur = con.cursor()
    result = cur.execute("SELECT * FROM Users")
    result = [x for x in result]
    result_id = [result[x][0] for x in range(len(result))]
    result_stat = [result[x][1] for x in range(len(result))]
    con.close()
    return [result_id, result_stat]


def change_status(id, status):
    con = sqlite3.connect("users.db")
    cur = con.cursor()
    cur.execute("UPDATE Users SET status = ? WHERE id = ?", (status, id))
    con.commit()
    con.close()


def main():
    token = 'fb848191c43352433e5f470f5f5324f3c4bdc761728f8eff388eca7d4cdb4d6164c6cb75b37db1d623738'
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    wikipedia.set_lang("ru")
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            print('id{}: "{}"'.format(event.user_id, event.text))
            ask = event.text.lower().split()
            keyboard = vk_keyboard("type")
            empty_keyboard = create_empty_keyboard()
            users = check_user()
            users_id = users[0]
            users_status = users[1]
            if "стоп" in ask:
                main()
            if ("назад" in ask) and (users_status[users_id.index(int(event.user_id))] != "type"):
                if (int(event.user_id) in users_id) and (users_status[users_id.index(int(event.user_id))] == "more"):
                    change_status(int(event.user_id), "type")
                elif (int(event.user_id) in users_id) and \
                        (users_status[users_id.index(int(event.user_id))] == "достопримечательности" or
                         users_status[users_id.index(int(event.user_id))] == "музеи" or
                         users_status[users_id.index(int(event.user_id))] == "галереи"):
                    change_status(int(event.user_id), "type")
                    try:
                        send_message(vk, event.user_id, "Выбери то, что хочешь посмотреть!", keyboard)
                        if event.user_id in users_id:
                            change_status(int(event.user_id), "type")
                        else:
                            add_users_data(int(event.user_id), "type")
                    except Exception as exc:
                        print("Ошибка: ", exc)
                continue
            if "привет" in ask:
                try:
                    send_message(vk, event.user_id, "Привет!", keyboard)
                    if event.user_id in users_id:
                        change_status(int(event.user_id), "type")
                    else:
                        add_users_data(int(event.user_id), "type")
                except Exception as exc:
                    print("Ошибка: ", exc)
            elif "достопримечательности" in ask:
                try:
                    keyboard = vk_keyboard("other")
                    send_message(vk, event.user_id,
                                 "Напиши название города, достопримечательности которого ты бы хотел посмотреть.",
                                 keyboard)
                    if event.user_id in users_id:
                        change_status(int(event.user_id), "достопримечательности")
                    else:
                        add_users_data(int(event.user_id), "достопримечательности")
                except Exception as exc:
                    print("Ошибка: ", exc)
            elif "музеи" in ask:
                try:
                    keyboard = vk_keyboard("other")
                    send_message(vk, event.user_id,
                                 "Напиши название города, музеи которого ты бы хотел посмотреть.", keyboard)
                    if event.user_id in users_id:
                        change_status(int(event.user_id), "музеи")
                    else:
                        add_users_data(int(event.user_id), "музеи")
                except Exception as exc:
                    print("Ошибка: ", exc)
            elif "галереи" in ask:
                try:
                    keyboard = vk_keyboard("other")
                    send_message(vk, event.user_id,
                                 "Напиши название города, галереи которого ты бы хотел посмотреть.", keyboard)
                    if event.user_id in users_id:
                        change_status(int(event.user_id), "галереи")
                    else:
                        add_users_data(int(event.user_id), "галереи")
                except Exception as exc:
                    print("Ошибка: ", exc)
            elif (int(event.user_id) in users_id) and \
                    (users_status[users_id.index(int(event.user_id))] == "достопримечательности"
                     or users_status[users_id.index(int(event.user_id))] == "музеи"
                     or users_status[users_id.index(int(event.user_id))] == "галереи"):
                try:
                    orgs = get_response(users_status[users_id.index(int(event.user_id))] + ask[0])
                    text = ''
                    for i in range(len(orgs)):
                        text += '{}. {}\n'.format(i + 1, orgs[i])
                    text += "Напиши цифру от 1 до 10 или нажми кнопку на клавиатуре и я расскажу больше об этом месте"
                except:
                    text = "Извините, я не нашел ничего по вашему запросу :("
                try:
                    change_status(event.user_id, "more")
                    try:
                        keyboard = vk_keyboard("more", orgs)
                        send_message(vk, event.user_id, text, keyboard)
                    except:
                        send_message(vk, event.user_id, text, empty_keyboard)
                    if event.user_id in users_id:
                        change_status(int(event.user_id), "more")
                except Exception as exc:
                    print("Ошибка: ", exc)
            elif (int(event.user_id) in users_id) and (users_status[users_id.index(int(event.user_id))] == "more"):
                if ask[0].isdigit():
                    try:
                        try:
                            wiki_text = wikipedia.summary(orgs[int(ask[0]) - 1])
                            send_message(vk, event.user_id, wiki_text, keyboard)
                        except:
                            send_message(vk, event.user_id, "Извините, я не смог найти информацию об этом месте :(",
                                         keyboard)
                        change_status(event.user_id, "type")
                    except Exception as exc:
                        print("Ошибка: ", exc)
                else:
                    try:
                        try:
                            wiki_text = " ".join(ask)
                            send_message(vk, event.user_id, wikipedia.summary(wiki_text), keyboard)
                        except:
                            send_message(vk, event.user_id, "Извините, я не смог найти информацию об этом месте :(",
                                         keyboard)
                        change_status(event.user_id, "type")
                    except Exception as exc:
                        print("Ошибка: ", exc)
            else:
                try:
                    send_message(vk, event.user_id, "Извините, я не понял вашего запроса, повторите попытку.")
                except Exception as exc:
                    print("Ошибка: ", exc)



if __name__ == '__main__':
    main()