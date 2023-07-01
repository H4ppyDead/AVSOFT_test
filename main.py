import os
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import urlopen
import threading
from urllib.error import URLError, HTTPError
import time


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
            return self.base_url + link
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

    def save_site_data(self, url, processing_time, link_count):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        file_name = f"{domain}.txt"
        file_path = os.path.join("sitemap", file_name).replace("\\", "/")
        abs_file_path = os.path.abspath(file_path)
        site_data = f"URL сайта: {url}\nВремя обработки: {processing_time:.2f} сек\nКол-во найденных ссылок: {link_count}\n\n"
        with open(abs_file_path, 'w', encoding='utf-8') as file:  # Открываем файл в режиме записи (write)
            file.write(site_data)


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
    result_file = f"{url.replace('http://', '').replace('https://', '').replace('/', '')}.txt"
    table_data.append([url, generator.processing_time, len(generator.internal_links), result_file])

# Выводим результаты в виде таблицы
print("URL сайта\t\tВремя обработки\tКол-во найденных ссылок\tИмя файла с результатом")
for data in table_data:
    print(f"{data[0]}\t\t{data[1]:.2f} сек\t\t{data[2]}\t\t\t{data[3]}")
