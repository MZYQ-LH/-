# -*- coding: utf-8 -*-
"""
猫眼电影详情页爬虫
功能：从电影网站爬取电影详情数据并保存到CSV文件
"""

import pandas as pd
import time
import re
import json
import csv
import os
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# 配置输入文件和输出文件的配置参数
URL_FILE = "URL_list.csv"  
OUTPUT_FILE = "猫眼电影_结果3.csv"  

# 配置输出CSV文件的列名
COLUMNS = [
    'title',          # 电影标题
    'movieImg',       # 电影图片
    'type',           # 电影类型
    'country',        # 制片国家/地区
    'duration',       # 电影时长
    'releaseTime',    # 上映时间
    'rate',           # 评分
    'summary',        # 电影简介
    'director',       # 导演
    'actors',         # 演员
    'firstBoxOffice', # 首日票房
    'allBoxOffice',   # 累计票房
    'detailUrl'       # 详情页URL
]

# 设定随机User-Agent列表，作用于反爬虫
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
]


def start_browser():
    """
    设定函数用于启动Chrome（谷歌）浏览器
    失败则返回None
    """
    try:
        # 配置Chrome驱动服务
        service = Service('./chromedriver.exe')
        
        # 设置浏览器选项
        option = Options()
        option.add_argument('--no-sandbox')  # 禁用沙盒模式
        option.add_argument('--disable-gpu')  # 禁用GPU加速
        option.add_argument('--window-size=1920,1080')  # 设置窗口大小
        option.add_experimental_option('excludeSwitches', ['enable-automation'])  # 排除自动化开关
        option.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')  # 随机User-Agent
        
        # 启动浏览器
        browser = webdriver.Chrome(service=service, options=option)
        
        # 隐藏webdriver属性，防止被网站检测
        browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        
        print("浏览器启动成功")
        return browser
    except Exception as e:
        print(f"浏览器启动失败: {e}")
        return None


def init_csv():
    """
    设定函数，初始化CSV文件
    """
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)


def get_movie_data(url, browser):
    """
    获取并解析电影数据
    参数：
        url: 电影详情页URL
        包含电影数据的字典
    """
    retry_count = 0
    while True:
        try:
            retry_count += 1
            if retry_count > 1:
                print(f"   第 {retry_count} 次尝试...")
            
            # 打开电影详情页
            browser.get(url)
            time.sleep(2)  # 等待页面加载
            
            # 获取页面源代码
            html = browser.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 初始化数据字典
            data = {col: '' for col in COLUMNS}
            data['detailUrl'] = url
            data['rate'] = 0
            data['firstBoxOffice'] = 0
            data['allBoxOffice'] = 0
            
            # 从JSON数据中提取信息
            script = soup.find('script', id='pageData', type='application/json')
            page_data = json.loads(script.string) if script and script.string else {}
            
            # 提取基本信息
            data['title'] = page_data.get('movieName', '')
            if not data['title']:
                # 从HTML中提取标题
                title_elem = soup.find('h1', class_='navBarTitle')
                data['title'] = title_elem.get_text(strip=True) if title_elem else ''
            
            
            if not data['title']:
                print("未找到电影标题，继续尝试...")
                time.sleep(3)
                continue
            
            
            data['movieImg'] = page_data.get('movieImg', '')
            data['type'] = page_data.get('category', '').replace(',', '-')
            data['director'] = page_data.get('director', '')
            data['releaseTime'] = page_data.get('releaseDate', '')
            
            # 提取国家和时长
            duration_div = soup.find('div', class_='info-source-duration')
            if duration_div:
                text = duration_div.get_text(strip=True)
                parts = text.split('/')
                if len(parts) >= 2:
                    data['country'] = parts[0].strip()
                    match = re.search(r'(\d+)', parts[1])
                    data['duration'] = match.group(1) if match else ''
            
            # 提取评分
            rate_elem = soup.find('span', class_='rating-num')
            if rate_elem:
                try:
                    data['rate'] = int(float(rate_elem.get_text(strip=True)) * 10)
                except:
                    pass
            
            # 提取电影简介
            for detail_item in soup.find_all('article', class_='detail-item'):
                title_div = detail_item.find('div', class_='detail-block-title')
                content_div = detail_item.find('div', class_='detail-block-content')
                if title_div and content_div and '影片简介' in title_div.get_text():
                    data['summary'] = content_div.get_text(strip=True)
                    break
            
            # 提取演员列表
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
            
            # 提取票房数据
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
            
            print(f"   成功获取: {data['title']}")
            return data
            
        except Exception as e:
            print(f"   错误: {e}")
            print("   3秒后继续尝试...")
            time.sleep(3)


def save_data(data):
    """
    设定函数，保存数据到CSV文件
    参数：
        data: 包含电影数据的字典
    返回：
        bool: 保存是否成功
    """
    if not data:
        return False
    
    # 按列顺序准备数据
    row = [data[col] for col in COLUMNS]
    
    try:
        with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        return True
    except Exception as e:
        print(f"保存出错: {e}")
        return False


def main():
    """
    主函数：读取URL列表并爬取电影详情
    """
    print("=" * 60)
    print("猫眼电影详情爬虫")
    print("=" * 60)
    
    # 初始化CSV文件
    init_csv()
    
    # 读取URL文件
    try:
        df_urls = pd.read_csv(URL_FILE)
        total = len(df_urls)
        print(f"\n已经获取到URL")
    except FileNotFoundError:
        print(f"找不到文件 {URL_FILE}")
        return
    except Exception as e:
        print(f"读取文件出错: {e}")
        return
    
    # 启动浏览器
    browser = start_browser()
    if not browser:
        return
    
    # 设置爬取范围用于演示
    try:
        start = int(input(f"从第几个开始 (1-{total}): ") or "1") - 1
        end = int(input(f"到第几个结束 (1-{total}): ") or str(min(3, total)))
    except ValueError:
        print("输入无效，使用默认值")
        start, end = 0, min(3, total)
    start, end = max(0, start), min(end, total)
    
    print(f"\n爬取第 {start+1} 到 {end} 个")
    
    # 统计成功数量
    success = 0
    
    # 遍历URL列表
    for i in range(start, end):
        row = df_urls.iloc[i]
        url = row.get('detail_url', '')
        print(f"\n[{i+1}/{end}] 处理电影...")
        print(f"   {url}")
        
        # 获取电影数据（无限重试直到成功）
        data = get_movie_data(url, browser)
        
        if data:
            # 尝试保存数据，直到成功
            while True:
                save_result = save_data(data)
                if save_result:
                    success += 1
                    print(f"   成功: {data['title'][:20]}...")
                    print(f"   导演: {data['director'][:15]}...")
                    print(f"   演员: {data['actors'][:30]}..." if data['actors'] else "   演员: 无")
                    print(f"   简介: {data['summary'][:40]}..." if data['summary'] else "   简介: 无")
                    print(f"   票房: {data['allBoxOffice']}万")
                    # 成功后等待0.8-2秒再处理下一个
                    time.sleep(random.uniform(0.8, 2))
                    break
                else:
                    print("   继续尝试保存...")
                    time.sleep(3)
    
    # 关闭浏览器
    browser.quit()
    print("\n浏览器已关闭")
    
    # 显示爬取结果
    print(f"\n完成！保存至: {OUTPUT_FILE}")
    print(f"   共 {success} 条数据")


if __name__ == '__main__':
    main()
