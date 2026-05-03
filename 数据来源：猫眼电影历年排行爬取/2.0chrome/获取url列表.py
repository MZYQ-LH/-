# crawl_urls.py - 爬取电影 URL 链接
import requests
import pandas as pd
import time
import random
from bs4 import BeautifulSoup

# 配置参数（年份区间，产出文件名）
# 让用户输入年份范围
try:
    START_YEAR = int(input("请输入起始年份 (例如: 2011): ") or "2011")
    END_YEAR = int(input("请输入结束年份 (例如: 2026): ") or "2026")
    # 确保起始年份小于等于结束年份
    if START_YEAR > END_YEAR:
        print("起始年份不能大于结束年份，使用默认值 2011-2026")
        START_YEAR, END_YEAR = 2011, 2026
except ValueError:
    print("输入无效，使用默认值 2011-2026")
    START_YEAR, END_YEAR = 2011, 2026
OUTPUT_FILE = "URL_list.csv"

# 设置请求头配置用于反爬机制（用户代理、接受类型、来源页）
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Referer': 'https://piaofang.maoyan.com/rankings',
}

def fetch_year_page(year, session):
    """获取指定年份的排行榜页面"""
    url = "https://piaofang.maoyan.com/rankings/year"
    params = {'year': year, 'limit': 300, 'tab': '1', 'WuKongReady': 'h5'}
    
    # 设定重试机制和等待时间用于规避
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
    """解析HTML页面，提取电影URL信息"""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    movies = []
    rows = soup.find_all('ul', class_='row')
    
    for row in rows:
        try:
            data_com = row.get('data-com', '')
            if "href:'" in data_com:
                href = data_com.split("href:'")[1].split("'")[0]
                movie_id = href.split('/movie/')[-1].split('?')[0] if '/movie/' in href else ''
                
                # 提取电影名称
                title_p = row.find('p', class_='first-line')
                title = title_p.get_text(strip=True) if title_p else ''
                
                # 提取上映日期
                date_p = row.find('p', class_='second-line')
                release_date = date_p.get_text(strip=True).replace(' 上映', '') if date_p else ''
                
                # 构建电影信息字典
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
    """主函数：爬取所有年份的电影URL并保存"""
    print("=" * 60)
    print("猫眼电影 URL 爬虫")
    print(f"年份范围：{START_YEAR} - {END_YEAR}")
    print("=" * 60)
    
    session = requests.Session()
    all_movies = []
    
    # 遍历每个年份
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"\n正在爬取 {year} 年...", end=' ')
        html = fetch_year_page(year, session)
        movies = parse_year_page(html, year)
        all_movies.extend(movies)
        print(f"完成，共 {len(movies)} 条")
        time.sleep(random.uniform(1, 2))
    
    # 保存为CSV文件
    if all_movies:
        df = pd.DataFrame(all_movies)
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("\n" + "=" * 60)
        print(f"爬取完成！共 {len(df)} 条电影 URL")
        print(f"文件保存至：{OUTPUT_FILE}")
        print("=" * 60)
        print("\n数据预览：")
        print(df.head())
    else:
        print("\n未获取到数据")

if __name__ == "__main__":
    main()
