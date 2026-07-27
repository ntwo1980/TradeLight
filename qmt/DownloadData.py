import requests
import json
from bs4 import BeautifulSoup

# 1. 设置基金页面地址
fund_code = "159985"
url = "https://www.chinaamc.com/fund/159985/index.shtml"

# 2. 发送请求
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
response = requests.get(url, headers=headers, timeout=20)
response.raise_for_status()

try:
    # 华夏基金页面的 table2 为“历史净值”表，第一行是最新净值记录。
    soup = BeautifulSoup(response.content, 'html.parser')
    latest_row = soup.select_one('.table2 .tb .tr')
    if latest_row is None:
        raise ValueError("未找到历史净值表的最新记录")

    cells = [cell.get_text(strip=True) for cell in latest_row.select('.td')]
    if len(cells) < 2:
        raise ValueError("最新净值记录格式不完整")

    nav_date, latest_nav = cells[0], cells[1]
    latest_nav = float(latest_nav)
    print(f"最新净值：{latest_nav}（{nav_date}）")

    # ---------------------------------------------------------
    # 🔴 新增逻辑：获取当前日期并覆盖写入 JSON 文件
    # ---------------------------------------------------------
    # 定义目标文件路径
    file_path = r"D:\君弘君智交易系统\bin.x64\159985SZ.json"

    # 构造要写入的 JSON 数据字典
    json_data = {
        "net_value": latest_nav,
        "date": nav_date
    }

    try:
        # 使用 'w' 模式直接覆盖写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        print(f"成功：已将最新净值 {latest_nav} 和日期 {nav_date} 覆盖写入 {file_path}")

    except PermissionError:
        print(f"权限错误：无法写入文件，请检查文件是否被交易系统占用或权限设置。")
    except Exception as e:
        print(f"写入JSON时发生未知错误：{e}")

except Exception as e:
    print("解析失败：", e)
