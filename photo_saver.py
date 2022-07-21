import json
import time
import tqdm
import requests
from pprint import pprint


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {'access_token': token, 'v': version}

    def save_photos(self, owner_id=None):
        album = ''
        photos_catalog = []
        while not album:
            album_name = input('Откуда будем сохранять фото?\nВведите цифру, где:\n1 - со стены;\n2 - фото '
                               'профиля;\n3 - сохраненные фотографии.\nВаш ввод: ')
            if album_name == '1':
                album = 'wall'
            elif album_name == '2':
                album = 'profile'
            elif album_name == '3':
                album = 'saved'
            else:
                print('\nНедопустимый параметр ввода, выберите вариант из предложенных, введите цифру и нажмите Enter.')
        photos_url = self.url + 'photos.get'
        photos_params = {'owner_id': owner_id, 'album_id': album, 'extended': '1', 'photo_sizes': '1'}
        res = requests.get(photos_url, params={**self.params, **photos_params}).json()
        if 'error' in res:
            pprint(f'Возникла ошибка: код ошибки {res["error"]["error_code"]}; {res["error"]["error_msg"]}')
        else:
            photos_in_album_quantity = len(res['response']['items'])
            amount = int(input('Введите количество фото, которые нужно сохранить.\nВаш ввод: '))
            if amount > photos_in_album_quantity:
                print(f'\nВ выбранном разделе нет такого количества изображений! Там всего {photos_in_album_quantity} '
                      f'фото.')
                # тут было бы здорово реализовать повторный запрос вводы количества фото для загрузки, но я пока так не
                # умею, хотя попробовал через вызов self.save_photos()
            else:
                link = ''
                img_max_size = 0
                with tqdm.tqdm(desc='Формирую перечень фотографий для передачи на Яндекс.Диск', leave=True,
                               total=amount, mininterval=0.5, bar_format='{desc} {percentage:2.0f} %') as pbar:
                    for names in range(amount):
                        name = ''
                        img_size = 0
                        for dimensions in res['response']['items'][names]['sizes']:
                            img_height = dimensions.get('height')
                            img_width = dimensions.get('width')
                            img_size = img_height * img_width
                            link = dimensions.get('url')
                            if img_size == 0:
                                choice = res['response']['items'][names]['sizes'][-1]
                                link = choice['url']
                                name = str(res['response']['items'][names].get('likes').get('count'))
                            else:
                                if img_size > img_max_size:
                                    img_max_size = img_size
                                    link = dimensions.get('url')
                                else:
                                    img_max_size = 0
                                    name = str(res['response']['items'][names].get('likes').get('count'))
                                    continue
                        photos_catalog.append({'file_name': name, 'link': link, 'size': str(img_size) + ' pix'})
                        time.sleep(0.125)
                        pbar.update(1)
            return tuple(photos_catalog)


class YaUploader:
    url = 'https://cloud-api.yandex.net/v1/disk/resources/'

    def __init__(self, token):
        self.token = token
        self.headers = {'Authorization': f'OAuth {self.token}', 'Content-Type': 'application/json'}

    def create_folder_on_yadisk(self):
        folder_name = input(f'Дайте название для создаваемой на Яндекс.Диск папки.\nВаш ввод: ')
        params = {'path': folder_name}
        requests.put(self.url, params=params, headers=self.headers)
        return folder_name

    def upload_by_url(self, data_list):
        if not data_list:
            print(f'Не получены данные от Вконтакте. Проверьте корректность ввода.')
        else:
            files_info = []
            folder = self.create_folder_on_yadisk()
            url_for_upload_by_url = self.url + 'upload'
            with tqdm.tqdm(total=len(data_list), bar_format='{desc} {percentage:2.0f} %', leave=True,
                           desc='Загружаю фото на Яндекс.Диск') as pbar:
                for objects in data_list:
                    properties = {'file_name': str(objects.get('file_name')), 'size': str(objects.get('size'))}
                    files_info.append(properties)
                    photo_name = f'{folder}/{objects.get("file_name")}'
                    params = {'path': photo_name, 'url': objects.get('link')}
                    response = requests.post(url_for_upload_by_url, params=params, headers=self.headers)
                    response.raise_for_status()
                    pbar.update(1)
                    with open('log.txt', 'a', encoding='utf-8') as log:
                        log_data = f'{time.asctime()} ***** : В папку {folder} на Яндекс.Диск успешно загружен файл ' \
                                   f'{objects.get("file_name")}\n'
                        log.write(log_data)
                    time.sleep(0.05)
                with open('report.json', 'a', encoding='utf-8') as target:
                    json.dump(files_info, target, indent=4)
            print(f'Фотографии успешно загружены на Яндекс.Диск в папку "{folder}".\nХронология процесса записана в '
                  f'файл "log.txt".\nСписок сохраненных фото находится в файле "report.json".')
            return target


if __name__ == '__main__':
    with open('vk.txt', 'r') as f1:
        tok_1 = f1.read().strip()
    with open('ya.txt', 'r') as f2:
        tok_2 = f2.read().strip()

    user_id = input(f'Введите цифровой номер пользователя VK:\n')
    vk_req = VkUser(tok_1, '5.131')
    ya_req = YaUploader(tok_2)
    data = vk_req.save_photos(user_id)
    ya_req.upload_by_url(data)
