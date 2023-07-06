import os
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen
import threading
from urllib.error import URLError, HTTPError
import time
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib.pyplot import annotate
import numpy as np



class LinkParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    link = self.normalize_link(attr[1].strip())
                    if link:
                        self.links.add(link)

    def normalize_link(self, link):
        if link.startswith('/'):
            return urljoin(self.base_url, link)
        elif link.startswith(self.base_url):
            return link
        else:
            return None


class SiteMapGenerator:
    def __init__(self, base_url):
        self.base_url = base_url
        self.visited_links = set()
        self.internal_links = set()
        self.lock = threading.Lock()
        self.processing_time = None

    def process_url(self, url):
        try:
            url = url.encode('ascii', 'ignore').decode('ascii')  # Преобразование URL в кодировку ASCII

            with urlopen(url) as response:
                if response.getcode() == 200:
                    content = response.read().decode()
                    parser = LinkParser(url)
                    parser.feed(content)
                    links = parser.links

                    internal_links = self.get_internal_links(links)
                    with self.lock:
                        self.internal_links.update(internal_links)
                    return links
                else:
                    print(f"Failed to retrieve page for URL: {url}")
        except (URLError, HTTPError, socket.error) as e:
            print(f"Error occurred while processing URL: {url}")
            print(f"Exception: {e}")
            return []

    def get_internal_links(self, links):
        internal_links = set()
        for link in links:
            if link.startswith(self.base_url) and link != self.base_url:
                internal_links.add(link)
        return internal_links

    def generate_site_map(self):
        start_time = time.time()  # Записываем время начала обработки сайта
        links = self.process_url(self.base_url)
        end_time = time.time()  # Записываем время окончания обработки сайта
        self.processing_time = end_time - start_time  # Вычисляем время обработки
        self.save_site_data(self.base_url, self.processing_time, len(links))  # Сохраняем данные сайта
        self.save_links_to_file(links)  # Сохраняем ссылки в файл

    def save_site_data(self, url, processing_time, link_count):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        file_name = f"{domain}.txt"
        file_path = os.path.join("sitemap", file_name).replace("\\", "/")
        abs_file_path = os.path.abspath(file_path)
        site_data = f"URL сайта: {url}\nВремя обработки: {processing_time:.2f} сек\nКол-во найденных ссылок: {link_count}\n\n"
        with open(abs_file_path, 'w', encoding='utf-8') as file:  # Открываем файл в режиме записи (write)
            file.write(site_data)

    def save_links_to_file(self, links):
        parsed_url = urlparse(self.base_url)
        domain = parsed_url.netloc
        file_name = f"{domain}_links.txt"
        file_path = os.path.join("sitemap", file_name).replace("\\", "/")
        abs_file_path = os.path.abspath(file_path)
        with open(abs_file_path, 'w', encoding='utf-8') as file:
            for link in links:
                file.write(link + "\n")

    def load_links_from_file(self):
        parsed_url = urlparse(self.base_url)
        domain = parsed_url.netloc
        file_name = f"{domain}_links.txt"
        file_path = os.path.join("sitemap", file_name).replace("\\", "/")
        abs_file_path = os.path.abspath(file_path)
        with open(abs_file_path, 'r', encoding='utf-8') as file:
            links = [line.strip() for line in file.readlines() if line.strip()]
        return links

    def build_site_map(self, depth=2):
        site_map = {self.base_url: []}  # Структура карты сайта
        self._traverse_site_map(self.base_url, site_map, depth)
        return site_map

    def _traverse_site_map(self, url, site_map, depth):
        if depth == 0:
            return

        if url not in site_map:
            links = self.load_links_from_file()  # Загружаем ссылки из файла
            site_map[url] = links
            for link in links:
                self._traverse_site_map(link, site_map, depth - 1)



# Основной код
websites = [
    "http://crawler-test.com/",
    "http://google.com/",
    "https://vk.com",
    "https://dzen.ru",
    "https://stackoverflow.com"
]

table_data = []
for url in websites:
    generator = SiteMapGenerator(url)
    generator.generate_site_map()
    result_file = f"{url.replace('http://', '').replace('https://', '').replace('/', '')}_links.txt"
    table_data.append([url, generator.processing_time, len(generator.internal_links), result_file])



def load_links_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        links = file.read().splitlines()
    return links



def draw_site_map(url, links):
    plt.figure(figsize=(10, 10))
    plt.title(f"Site Map for {url}")

    # Отрисовка главного сайта
    main_width = 0.4
    main_height = 0.2
    main_radius = np.sqrt(main_width**2 + main_height**2) / 2  # Расчет радиуса главного эллипса
    main_angle = np.pi / 2  # Угол положения главного эллипса
    main_x = main_radius * np.cos(main_angle)
    main_y = main_radius * np.sin(main_angle)
    main_ellipse = Ellipse((main_x, main_y), main_width, main_height, facecolor='lightblue', edgecolor='black')
    plt.gca().add_patch(main_ellipse)
    plt.text(main_x, main_y, url, ha='center', va='center', fontsize=8, fontweight='bold')

    # Отрисовка ссылок от главного сайта
    link_radius = 1.2 * main_radius  # Расстояние от главного эллипса до ссылок
    link_angle = np.linspace(0, 2*np.pi, len(links) + 1)[:-1]  # Углы положения ссылок
    link_x = link_radius * np.cos(link_angle)
    link_y = link_radius * np.sin(link_angle)

    for i, link in enumerate(links):
        link_ellipse = Ellipse((link_x[i], link_y[i]), main_width, main_height, facecolor='lightgray', edgecolor='black')
        plt.gca().add_patch(link_ellipse)

        # Расчет координат стрелки
        x_start = main_x + main_width/2 * np.cos(link_angle[i])
        y_start = main_y + main_height/2 * np.sin(link_angle[i])
        x_end = link_x[i] - main_width/2 * np.cos(link_angle[i])
        y_end = link_y[i] - main_height/2 * np.sin(link_angle[i])

        # Отрисовка стрелки
        arrow_props = dict(arrowstyle="->", linewidth=1.5, color='black')
        plt.annotate('', xy=(x_end, y_end), xytext=(x_start, y_start), arrowprops=arrow_props)

        plt.text(link_x[i], link_y[i], link, ha='center', va='center', fontsize=8)

    plt.axis('off')
    plt.show()

# Список сайтов и пути к файлам с ссылками
websites = [
    ("http://crawler-test.com", "D:/Проекты/Тестовое/AVSOFT_test/sitemap/crawler-test.com_links.txt"),
    ("http://google.com", "D:/Проекты/Тестовое/AVSOFT_test/sitemap/google.com_links.txt"),
    ("https://vk.com", "D:/Проекты/Тестовое/AVSOFT_test/sitemap/vk.com_links.txt"),
    ("https://dzen.ru", "D:/Проекты/Тестовое/AVSOFT_test/sitemap/dzen.ru_links.txt"),
    ("https://stackoverflow.com", "D:/Проекты/Тестовое/AVSOFT_test/sitemap/stackoverflow.com_links.txt")
]
# Если хотите посмотреть на странные фигуры, то можете раскомментировать 
# for website, links_file in websites:
#     links = load_links_from_file(links_file)
#     draw_site_map(website, links)
    
# Выводим результаты в виде таблицы
print("URL сайта\t\tВремя обработки\tКол-во найденных ссылок\tИмя файла с результатом")
for data in table_data:
    print(f"{data[0]}\t\t{data[1]:.2f} сек\t\t{data[2]}\t\t\t{data[3]}")

