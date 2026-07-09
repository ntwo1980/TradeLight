import requests
import re
import json
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime  # 新增：导入datetime模块

# 1. 设置请求参数
fund_code = "159985"
url = "http://fund.eastmoney.com/f10/F10DataApi.aspx"
params = {
    "type": "lsjz",
    "code": fund_code,
    "page": 1,
    "per": 20
}

# 2. 发送请求
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
response = requests.get(url, params=params, headers=headers)

# 3. 提取 HTML 表格字符串
raw_content = response.content
# 使用字节正则匹配提取 content 中的内容
content_match = re.search(rb'content\s*:\s*"(.+?)"\s*,\s*records', raw_content, re.DOTALL)
if not content_match:
    print("未找到数据，请检查基金代码或网络")
    exit()

html_bytes = content_match.group(1)

# 4. 修复转义字符并解码为 UTF-8 字符串
html_bytes = html_bytes.replace(b'\\"', b'"')
html_bytes = html_bytes.replace(b'\\\\', b'\\')
html_string = html_bytes.decode('utf-8')

# ---------------------------------------------------------
# 🔴 核心修复：使用 BeautifulSoup 解析 HTML 表格
# ---------------------------------------------------------
try:
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_string, 'html.parser')
    table = soup.find('table')

    # 提取表头
    headers_th = table.find_all('th')
    columns = [th.get_text() for th in headers_th]

    # 提取表格数据行
    rows = []
    for tr in table.find_all('tr')[1:]: # 跳过表头行
        tds = tr.find_all('td')
        row = [td.get_text() for td in tds]
        rows.append(row)

    # 转换为 Pandas DataFrame
    data = pd.DataFrame(rows, columns=columns)

    # 5. 数据清洗与格式化
    data["净值日期"] = pd.to_datetime(data["净值日期"])

    latest_nav = data.iloc[0]['单位净值']
    print("第一条记录的单位净值为：", latest_nav)

    # ---------------------------------------------------------
    # 🔴 新增逻辑：获取当前日期并覆盖写入 JSON 文件
    # ---------------------------------------------------------
    # 定义目标文件路径
    file_path = r"D:\君弘君智交易系统\bin.x64\159985SZ.json"

    # 获取当前日期并格式化为字符串 (例如: "2026-07-09")
    current_date = datetime.now().strftime("%Y-%m-%d")

    # 构造要写入的 JSON 数据字典
    json_data = {
        "net_value": float(latest_nav),
        "date": current_date  # 新增：写入当前日期
    }

    try:
        # 使用 'w' 模式直接覆盖写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        print(f"成功：已将最新净值 {latest_nav} 和日期 {current_date} 覆盖写入 {file_path}")

    except PermissionError:
        print(f"权限错误：无法写入文件，请检查文件是否被交易系统占用或权限设置。")
    except Exception as e:
        print(f"写入JSON时发生未知错误：{e}")

except Exception as e:
    print("解析失败：", e)
