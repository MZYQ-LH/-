# crawl_urls.py - 爬取电影 URL 链接
import requests
import pandas as pd
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime

# 配置
START_YEAR, END_YEAR = 2011, 2026
OUTPUT_FILE = f"movie_urls_{datetime.now().strftime('%Y%m%d')}.csv"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Referer': 'https://piaofang.maoyan.com/rankings',
}

def fetch_year_page(year, session):
    """获取年份排行榜页面"""
    url = "https://piaofang.maoyan.com/rankings/year"
    params = {'year': year, 'limit': 300, 'tab': '1', 'WuKongReady': 'h5'}
    
    for _ in range(3):
        try:
            resp = session.get(url, params=params, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return resp.text
            time.sleep(2)
        except:
            time.sleep(2)
    return None

def parse_year_page(html, year):
    """解析年份页面，提取电影 URL"""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    movies = []
    rows = soup.find_all('ul', class_='row')
    
    for row in rows:
        try:
            # 提取 data-com 中的 href
            data_com = row.get('data-com', '')
            if "href:'" in data_com:
                href = data_com.split("href:'")[1].split("'")[0]
                movie_id = href.split('/movie/')[-1].split('?')[0] if '/movie/' in href else ''
                
                # 提取电影名
                title_p = row.find('p', class_='first-line')
                title = title_p.get_text(strip=True) if title_p else ''
                
                # 提取上映日期
                date_p = row.find('p', class_='second-line')
                release_date = date_p.get_text(strip=True).replace(' 上映', '') if date_p else ''
                
                # 提取票房数据
                cols = row.find_all('li')
                
                movies.append({
                    'year': year,
                    'title': title,
                    'movie_id': movie_id,
                    'release_date': release_date,
                    'detail_url': f"https://piaofang.maoyan.com{href}" if href else ''
                })
        except:
            continue
    
    return movies

def main():
    print("=" * 60)
    print("🎬 猫眼电影 URL 爬虫")
    print(f"📅 年份范围：{START_YEAR} - {END_YEAR}")
    print("=" * 60)
    
    session = requests.Session()
    all_movies = []
    
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"\n📌 爬取 {year} 年...", end=' ')
        html = fetch_year_page(year, session)
        movies = parse_year_page(html, year)
        all_movies.extend(movies)
        print(f"✅ {len(movies)} 条")
        time.sleep(random.uniform(1, 2))
    
    # 保存 CSV
    if all_movies:
        df = pd.DataFrame(all_movies)
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("\n" + "=" * 60)
        print(f"🎉 完成！共 {len(df)} 条电影 URL")
        print(f"📂 保存至：{OUTPUT_FILE}")
        print("=" * 60)
        print("\n📋 数据预览:")
        print(df.head())
    else:
        print("\n❌ 未获取到数据")

if __name__ == "__main__":
    main()