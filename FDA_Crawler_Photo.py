import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin

# FDA召回信息主页，包含 Food & Beverages 类别过滤
FDA_RECALLS_URL = "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts?product_type=Food%20%26%20Beverages"

# AJAX URL，用于分页数据请求
AJAX_URL = "https://www.fda.gov/datatables/views/ajax"

# 伪装请求头，避免被反爬
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/91.0.4472.124 Safari/537.36")
}

def flatten_list(lst):
    """递归将嵌套列表中的所有元素转换为字符串并展开"""
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(str(item))
    return result

def fetch_food_recall_links_static(url):
    """从静态加载的第一页获取召回公告链接"""
    recall_links = []
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return recall_links

    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.select("#datatable tbody tr")
    for row in rows:
        product_type_td = row.select_one("td.views-field-field-regulated-product-field")
        if product_type_td and "Food & Beverages" in product_type_td.get_text(strip=True):
            link_tag = row.select_one("a[href^='/safety/recalls-market-withdrawals-safety-alerts/']")
            if link_tag:
                href = link_tag["href"]
                full_url = urljoin("https://www.fda.gov", href)
                if full_url not in recall_links:
                    recall_links.append(full_url)
    return recall_links

def fetch_food_recall_links_ajax(page):
    """
    模拟 AJAX 请求获取召回公告链接。
    参数 page 表示分页索引，从 0 开始。
    """
    params = {
        "_drupal_ajax": 1,
        "_wrapper_format": "drupal_ajax",
        "pager_element": 0,
        "view_args": "",
        "view_base_path": "safety/recalls-market-withdrawals-safety-alerts/datatables-data",
        "view_display_id": "recall_datatable_block_1",
        "view_dom_id": "e0810721f0b8505216c9f7f83ce3d79c4f1db1d26234f5a2eb32b3696f2e00eb",
        "view_name": "recall_solr_index",
        "view_path": "/safety/recalls-market-withdrawals-safety-alerts",
        "page": page,
        "field_regulated_product_field": "2323"  # Food & Beverages 对应的值
    }
    recall_links = []
    try:
        response = requests.get(AJAX_URL, headers=HEADERS, params=params)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"AJAX 请求错误 (page {page}): {e}")
        return recall_links

    try:
        ajax_data = response.json()
    except json.JSONDecodeError as e:
        print(f"解析 AJAX 响应错误 (page {page}): {e}")
        return recall_links

    if isinstance(ajax_data, list):
        for command in ajax_data:
            if isinstance(command, dict) and "data" in command:
                data_field = command["data"]
                if isinstance(data_field, list):
                    flat_list = flatten_list(data_field)
                    html_fragment = "".join(flat_list)
                elif isinstance(data_field, str):
                    html_fragment = data_field
                else:
                    continue
                fragment_soup = BeautifulSoup(html_fragment, 'html.parser')
                rows = fragment_soup.select("tr")
                for row in rows:
                    product_type_td = row.select_one("td.views-field-field-regulated-product-field")
                    if product_type_td and "Food & Beverages" in product_type_td.get_text(strip=True):
                        link_tag = row.select_one("a[href^='/safety/recalls-market-withdrawals-safety-alerts/']")
                        if link_tag:
                            href = link_tag["href"]
                            full_url = urljoin("https://www.fda.gov", href)
                            if full_url not in recall_links:
                                recall_links.append(full_url)
    elif isinstance(ajax_data, dict) and "data" in ajax_data:
        data_field = ajax_data["data"]
        if isinstance(data_field, list):
            flat_list = flatten_list(data_field)
            html_fragment = "".join(flat_list)
        elif isinstance(data_field, str):
            html_fragment = data_field
        else:
            html_fragment = ""
        fragment_soup = BeautifulSoup(html_fragment, 'html.parser')
        rows = fragment_soup.select("tr")
        for row in rows:
            product_type_td = row.select_one("td.views-field-field-regulated-product-field")
            if product_type_td and "Food & Beverages" in product_type_td.get_text(strip=True):
                link_tag = row.select_one("a[href^='/safety/recalls-market-withdrawals-safety-alerts/']")
                if link_tag:
                    href = link_tag["href"]
                    full_url = urljoin("https://www.fda.gov", href)
                    if full_url not in recall_links:
                        recall_links.append(full_url)
    else:
        fragment_soup = BeautifulSoup(response.text, 'html.parser')
        rows = fragment_soup.select("tr")
        for row in rows:
            product_type_td = row.select_one("td.views-field-field-regulated-product-field")
            if product_type_td and "Food & Beverages" in product_type_td.get_text(strip=True):
                link_tag = row.select_one("a[href^='/safety/recalls-market-withdrawals-safety-alerts/']")
                if link_tag:
                    href = link_tag["href"]
                    full_url = urljoin("https://www.fda.gov", href)
                    if full_url not in recall_links:
                        recall_links.append(full_url)
    return recall_links

def fetch_recall_details(url):
    """爬取召回详情页面"""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"请求错误 {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # 1. 提取公司声明
    company_announcement_section = soup.find('h2', id='recall-announcement')
    company_announcement = "未找到公司声明。"
    if company_announcement_section:
        paragraphs = company_announcement_section.find_next_siblings('p')
        company_announcement = " ".join([p.get_text(strip=True) for p in paragraphs])

    # 2. 提取产品图片
    product_images = []
    image_section = soup.find('div', id='recall-photos')
    if image_section:
        img_tags = image_section.find_all('img')
        for img in img_tags:
            img_src = img.get('src', '')
            if img_src.startswith('/files'):
                img_src = urljoin("https://www.fda.gov", img_src)
            product_images.append(img_src)

    # 3. 提取产品详情信息
    details = {}
    description_list = soup.find('dl', class_='lcds-description-list--grid')
    if description_list:
        items = description_list.find_all(['dt', 'dd'])
        for i in range(0, len(items), 2):
            key = items[i].get_text(strip=True).replace(":", "")
            value = items[i+1].get_text(strip=True)
            details[key] = value

    return {
        'url': url,
        'company_announcement': company_announcement,
        'product_images': product_images,
        'product_details': details
    }

def main():
    all_links = set()

    # 抓取静态页面链接（第一页）
    static_links = fetch_food_recall_links_static(FDA_RECALLS_URL)
    all_links.update(static_links)
    print(f"静态页面共发现 {len(static_links)} 个链接.")

    # 抓取 AJAX 分页数据
    page = 0
    while True:
        ajax_links = fetch_food_recall_links_ajax(page)
        if not ajax_links:
            break
        new_links = set(ajax_links) - all_links
        if not new_links:
            break
        all_links.update(new_links)
        print(f"第 {page} 页 AJAX 抓取到 {len(new_links)} 个新链接，总共 {len(all_links)} 个链接")
        page += 1
        time.sleep(2)

    recall_links = list(all_links)
    print(f"总共发现 {len(recall_links)} 个食品召回公告链接")

    all_recall_details = []
    for idx, link in enumerate(recall_links):
        print(f"正在爬取 {idx+1}/{len(recall_links)}: {link}")
        details = fetch_recall_details(link)
        if details:
            all_recall_details.append(details)
        time.sleep(2)

    with open('all_food_beverage_recall_details.json', 'w', encoding='utf-8') as f:
        json.dump(all_recall_details, f, ensure_ascii=False, indent=4)
    print("所有召回详情已保存至 all_food_beverage_recall_details.json")

if __name__ == '__main__':
    main()











