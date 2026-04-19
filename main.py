import asyncio
import json
import shutil
import os
import re

from playwright.sync_api import sync_playwright
from playwright.sync_api import Error as PlaywrightError
from time import sleep

from aggregate_dispatcher import dispatch
from utils import deep_merge


class Parser:
    def __init__(self):
        self.url_blank = 'https://hackerone.com'
        self.url_cards = '/hacktivity/overview'
        self.headers = {
            'user_agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.140 '
                'Safari/537.36'
            ),
        }
        self.output_dir = 'researchers_info'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    @staticmethod
    def aggregate_user_data(path, output_filename='highlights.json'):
        final_data = {
            'profile': {},
            'memberships': {},
            'snapshot': {},
            'user_stats': {},
            'weakness_stats': {},
        }

        for filename in os.listdir(path):
            if not filename.endswith('.json') or filename == output_filename:
                continue

            filepath = os.path.join(path, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    new_data = dispatch(data)

                    if new_data:
                        deep_merge(final_data, new_data)
                except Exception as e:
                    print(f'Ошибка агрегации файла {filename}: {e}')

        output_path = os.path.join(path, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
        print(f'[+] Отчет создан: {output_path}')

    def scroll_to_bottom(self, page):
        last_height = page.evaluate("document.body.scrollHeight")
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def get_user_info(self, page, link, path):
        def intercept_response(response):
            if 'graphql' in response.url:
                try:
                    data = response.json()
                    count = len([f for f in os.listdir(path) if f.endswith('.json')])
                    filename = f'response_{count}.json'
                    filepath = os.path.join(path, filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    print(f"[+] Сохранено: {filename} в {path}")

                except (PlaywrightError, Exception) as e:
                    if "TargetClosedError" in str(e) or "Target page" in str(e):
                        return
                    print(f"Ошибка при получении ответа: {e}")

        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)
        page.on('response', intercept_response)

        try:
            page.goto(link, wait_until='load')
            self.scroll_to_bottom(page)
            sleep(3)
            try:
                hacktivity_link = link.split('?')[0].rstrip('/') + '/hacktivity?type=user'
                page.goto(hacktivity_link, wait_until='load')
                self.scroll_to_bottom(page)
                sleep(3)
            except:
                pass
        except:
            pass

        page.remove_listener('response', intercept_response)
        self.aggregate_user_data(path)

    def get_users_pages(self, page):
        user_page_links = []
        try:
            page.goto(self.url_blank + self.url_cards, wait_until='networkidle')

            locator = page.locator('div.pb-spacing-12 span.spec-user-mini-profile-tooltip a.daisy-link.routerlink.daisy-link')
            locator.first.wait_for(timeout=10000)
            page_links = locator.all()

            for page_link in page_links:
                href = self.url_blank + page_link.get_attribute('href')
                user_page_links.append(href[:-9:])
        except Exception as e:
            print(f'Ошибка при сборе карточек пользователей: {e}')

        user_page_links = list(set(user_page_links))
        return user_page_links

    def parse(self):
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False)
            context = browser.new_context(**self.headers)
            page = context.new_page()

            user_page_links = self.get_users_pages(page)

            for user_page_link in user_page_links:
                user_page_link += '/hacktivity?type=user'
                match = re.search(r'.com/([^?]+)', user_page_link)
                if match:
                    username = match.group(1)
                    path = os.path.join(self.output_dir, username)
                    self.get_user_info(page, user_page_link, path)


if __name__ == '__main__':
    parser = Parser()
    parser.parse()
