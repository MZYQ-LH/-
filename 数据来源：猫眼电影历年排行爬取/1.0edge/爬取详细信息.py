# -*- coding: utf-8 -*-
"""猫眼电影详情页爬虫"""
import pandas as pd
import time
import re
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL_FILE = "movie_urls_20260314.csv"
OUTPUT_FILE = "猫眼电影_结果.csv"

COLUMNS = ['title', 'movieImg', 'type', 'country', 'duration', 'releaseTime', 
           'rate', 'summary', 'director', 'actors', 'firstBoxOffice', 'allBoxOffice', 'detailUrl']


def start_browser():
    """启动Edge浏览器"""
    option = EdgeOptions()
    option.add_argument('--headless')
    option.add_argument('--no-sandbox')
    option.add_argument('--disable-gpu')
    option.add_argument('--window-size=1920,1080')
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    
    try:
        service = EdgeService('./msedgedriver.exe')
        browser = webdriver.Edge(service=service, options=option)
        browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        print("✅ 浏览器启动成功")
        return browser
    except Exception as e:
        print(f"❌ 浏览器启动失败: {e}")
        return None


def get_movie_data(url, browser):
    """获取并解析电影数据"""
    while True:
        try:
            browser.get(url)
            time.sleep(2)
            try:
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "navBarTitle"))
                )
            except:
                pass
            time.sleep(1)
            
            html = browser.page_source
            soup = BeautifulSoup(html, 'html.parser')
            data = {col: '' for col in COLUMNS}
            data['detailUrl'] = url
            data['rate'] = 0
            data['firstBoxOffice'] = 0
            data['allBoxOffice'] = 0
            
            script = soup.find('script', id='pageData', type='application/json')
            page_data = json.loads(script.string) if script and script.string else {}
            
            data['title'] = page_data.get('movieName', '')
            if not data['title']:
                title_elem = soup.find('h1', class_='navBarTitle')
                data['title'] = title_elem.get_text(strip=True) if title_elem else ''
            
            if not data['title']:
                raise Exception("无标题")
            
            data['movieImg'] = page_data.get('movieImg', '')
            data['type'] = page_data.get('category', '').replace(',', '-')
            data['director'] = page_data.get('director', '')
            data['releaseTime'] = page_data.get('releaseDate', '')
            
            duration_div = soup.find('div', class_='info-source-duration')
            if duration_div:
                text = duration_div.get_text(strip=True)
                parts = text.split('/')
                if len(parts) >= 2:
                    data['country'] = parts[0].strip()
                    match = re.search(r'(\d+)', parts[1])
                    data['duration'] = match.group(1) if match else ''
            
            rate_elem = soup.find('span', class_='rating-num')
            if rate_elem:
                try:
                    data['rate'] = int(float(rate_elem.get_text(strip=True)) * 10)
                except:
                    pass
            
            for detail_item in soup.find_all('article', class_='detail-item'):
                title_div = detail_item.find('div', class_='detail-block-title')
                content_div = detail_item.find('div', class_='detail-block-content')
                if title_div and content_div and '影片简介' in title_div.get_text():
                    data['summary'] = content_div.get_text(strip=True)
                    break
            
            actors = []
            celebrity_section = soup.find('section', class_='celebrity-section')
            if celebrity_section:
                for item in celebrity_section.find_all('div', class_='item')[:10]:
                    name_elem = item.find('p', class_='title ellipsis-1')
                    if name_elem:
                        actor_name = name_elem.get_text(strip=True)
                        if actor_name and actor_name != data['director']:
                            actors.append(actor_name)
            data['actors'] = '-'.join(actors) if actors else ''
            
            for row in soup.find_all('div', class_='info-detail-row'):
                for col in row.find_all('div', class_='info-detail-col'):
                    title = col.find('p', class_='info-detail-title')
                    content = col.find('p', class_='info-detail-content')
                    if title and content:
                        title_text = title.get_text(strip=True)
                        num = content.find('span', class_='detail-num')
                        unit = content.find('span', class_='detail-unit')
                        if num and unit:
                            try:
                                n = float(num.get_text(strip=True))
                                u = unit.get_text(strip=True)
                                value = int(n * 10000) if '亿' in u else int(n)
                                if '累计' in title_text:
                                    data['allBoxOffice'] = value
                                elif '首日' in title_text:
                                    data['firstBoxOffice'] = value
                            except:
                                pass
            
            return data
        except Exception as e:
            print(f"   🔄 重试: {e}")
            time.sleep(2)


def main():
    print("=" * 60)
    print("🎬 猫眼电影详情爬虫")
    print("=" * 60)
    
    df_urls = pd.read_csv(URL_FILE)
    total = len(df_urls)
    print(f"\n📊 共 {total} 个URL")
    
    browser = start_browser()
    if not browser:
        return
    
    try:
        start = int(input(f"从第几个开始 (1-{total}): ") or 1) - 1
        end = int(input(f"到第几个结束 (1-{total}): ") or 3)
    except:
        start, end = 0, 3
    start, end = max(0, start), min(end, total)
    
    print(f"\n🎯 爬取第 {start+1} 到 {end} 个")
    
    results = []
    
    for i in range(start, end):
        row = df_urls.iloc[i]
        url = row.get('detail_url', '')
        print(f"\n[{i+1}/{end}] {row.get('title', '未知')}")
        
        data = get_movie_data(url, browser)
        results.append(data)
        print(f"   ✅ {data['title'][:20]}...")
        print(f"   🎬 导演: {data['director'][:15]}...")
        print(f"   👥 演员: {data['actors'][:30]}..." if data['actors'] else "   👥 演员: 无")
        print(f"   📝 简介: {data['summary'][:40]}..." if data['summary'] else "   📝 简介: 无")
        print(f"   💰 票房: {data['allBoxOffice']}万")
    
    browser.quit()
    print("\n🔄 浏览器已关闭")
    
    if results:
        pd.DataFrame(results)[COLUMNS].to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"\n🎉 完成！保存至: {OUTPUT_FILE}")
        print(f"   共 {len(results)} 条数据")


if __name__ == '__main__':
    main()
