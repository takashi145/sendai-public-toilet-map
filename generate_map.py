import pandas as pd
from bs4 import BeautifulSoup
import folium
from folium.plugins import MarkerCluster
import os
from dotenv import load_dotenv
from datetime import datetime
import shutil

# ローカルで.envから読み込めるようにする
load_dotenv()

# マップhtml出力先
OUTPUT_DIR = 'dist'
OUTPUT_HTML = os.path.join(OUTPUT_DIR, 'index.html')

# NaNを-----に置換
def replace_nan(value):
  return '-----' if pd.isna(value) else value

CSV_URL = os.environ.get('SENDAI_PUBLIC_TOILET_CSV_URL')
if CSV_URL is None:
		raise ValueError("SENDAI_PUBLIC_TOILET_CSV_URLが設定されていません。")

# 地図作成
map = folium.Map(
  location=[38.258723,140.872241],
  height=600,
	width='100%',
  zoom_start=11
)

# 現在地表示ボタンの追加
folium.plugins.LocateControl(
  auto_start=False,
  strings={
    "title": "現在地を表示",
    "popup": "現在地"
  }
).add_to(map)

# 全画面表示ボタンの追加
folium.plugins.Fullscreen(
    position="topright",
    title="Expand me",
    title_cancel="Exit me",
    force_separate_button=True,
).add_to(map)

# データ取得日時
data_acquired_date = datetime.now().strftime('%Y年%m月%d日 %H:%M')

data = pd.read_csv(CSV_URL, encoding="utf-8")

marker_cluster = MarkerCluster(
    name='sendai toilet',
    overlay=True,
    control=False,
    icon_create_function=None
)

for _, row in data.iterrows():
  if (pd.isna(row['緯度']) or pd.isna(row['経度'])):
      continue

  marker = folium.Marker([row['緯度'], row['経度']])

  # トイレ設備情報のセクション作成
  toilet_info = ""

  # 男性トイレ情報
  try:
    if not pd.isna(row['男性トイレ総数']) and int(row['男性トイレ総数']) > 0:
      toilet_info += f"""
				<div class="toilet-section">
					<h4>🚹 男性トイレ</h4>
					<ul>
						<li>小便器: {replace_nan(row['男性トイレ数（小便器）'])}個</li>
						<li>和式: {replace_nan(row['男性トイレ数（和式）'])}個</li>
						<li>洋式: {replace_nan(row['男性トイレ数（洋式）'])}個</li>
					</ul>
				</div>
				"""
  except (ValueError, TypeError):
    pass

  # 女性トイレ情報
  try:
    if not pd.isna(row['女性トイレ総数']) and int(row['女性トイレ総数']) > 0:
      toilet_info += f"""
				<div class="toilet-section">
					<h4>🚺 女性トイレ</h4>
					<ul>
						<li>和式: {replace_nan(row['女性トイレ数（和式）'])}個</li>
						<li>洋式: {replace_nan(row['女性トイレ数（洋式）'])}個</li>
					</ul>
				</div>
				"""
  except (ValueError, TypeError):
    pass

  # 男女共用トイレ情報
  try:
    if not pd.isna(row['男女共用トイレ総数']) and int(row['男女共用トイレ総数']) > 0:
      toilet_info += f"""
				<div class="toilet-section">
					<h4>🚻 男女共用トイレ</h4>
					<ul>
						<li>和式: {replace_nan(row['男女共用トイレ数（和式）'])}個</li>
						<li>洋式: {replace_nan(row['男女共用トイレ数（洋式）'])}個</li>
					</ul>
				</div>
				"""
  except (ValueError, TypeError):
    pass

  # バリアフリー設備情報
  barrier_free_info = ""
  if not pd.isna(row['バリアフリートイレ数']) and int(row['バリアフリートイレ数']) > 0:
    barrier_free_info += f"<li>♿ バリアフリートイレ: {int(row['バリアフリートイレ数'])}個</li>"
  if not pd.isna(row['車椅子使用者用トイレ有無']) and row['車椅子使用者用トイレ有無'] == '有':
    barrier_free_info += "<li>♿ 車椅子使用者用トイレあり</li>"
  if not pd.isna(row['乳幼児用設備設置トイレ有無']) and row['乳幼児用設備設置トイレ有無'] == '有':
    barrier_free_info += "<li>👶 乳幼児用設備あり</li>"
  if not pd.isna(row['オストメイト設置トイレ有無']) and row['オストメイト設置トイレ有無'] == '有':
    barrier_free_info += "<li>🏥 オストメイト対応</li>"

  if barrier_free_info:
    barrier_free_info = f"""
    <div class="toilet-section">
      <h4>バリアフリー設備</h4>
      <ul>{barrier_free_info}</ul>
    </div>
    """

  time_info = ""
  if not pd.isna(row['利用開始時間']) or not pd.isna(row['利用終了時間']):
    time_info = f"<p><b>利用可能時間:</b> {replace_nan(row['利用開始時間'])} - {replace_nan(row['利用終了時間'])}</p>"
  if not pd.isna(row['利用可能時間特記事項']):
    time_info += f"<p><b>備考:</b> {row['利用可能時間特記事項']}</p>"

  popup = f"""
  <div id="popup">
    <div class="popup-content">
      <h3><ruby>{row['名称']}<rt>{replace_nan(row['名称_カナ'])}</rt></ruby></h3>
      <p><b>所在地:</b> {replace_nan(row['所在地_連結表記'])}</p>
      <p><b>建物名:</b> {replace_nan(row['建物名等(方書)'])}</p>
      <p><b>設置位置:</b> {replace_nan(row['設置位置'])}</p>
      {time_info}
      <p><b>トイレ設備情報:</b></p>
      <div class="toilet-info">
        {toilet_info}
        {barrier_free_info}
      </div>
    </div>
    <a href="http://local.google.co.jp/maps?q={row['所在地_連結表記']}" class="google-maps-link" target="_blank" rel="noopener noreferrer">📍 Googleマップで表示</a>
  </div>
  """
  folium.Popup(popup, max_width=400).add_to(marker)
  marker_cluster.add_child(marker)

marker_cluster.add_to(map)

# 出力ディレクトリを作成
os.makedirs(OUTPUT_DIR, exist_ok=True)

# main.cssをOUTPUT_DIRにコピー
shutil.copy('main.css', os.path.join(OUTPUT_DIR, 'main.css'))

map.save(OUTPUT_HTML)

with open(OUTPUT_HTML, 'r', encoding='utf-8') as file:
  soup = BeautifulSoup(file, 'html.parser')

title = soup.new_tag('title')
title.string = "仙台市公衆トイレマップ"
soup.head.append(title)

link = soup.new_tag('link', rel="stylesheet", href="main.css")
soup.head.append(link)

title = soup.new_tag('h1')
title.string = "仙台市公衆トイレマップ"
soup.body.insert(0, title)

data_date = f"""
<p id="data-date">データ取得日: {data_acquired_date}</p>
"""
soup.body.append(BeautifulSoup(data_date, 'html.parser'))

notice = """
<p id="notice">※このマップは仙台市のオープンデータ「公衆トイレ一覧」から毎週1回取得した情報を元に作成しています。<br />
データの取得タイミングや元データの更新状況により、最新の情報ではない可能性があります。</p>
"""
soup.body.append(BeautifulSoup(notice, 'html.parser'))

text = """
<p id="attribution">この「仙台市 公衆トイレマップ」は以下の著作物を改変して利用しています。<br>
公衆トイレ一覧、仙台市まちづくり政策局まちのデジタル推進課連携推進係、クリエイティブ・コモンズ表示2.1日本ライセンス
（<a href="https://creativecommons.org/licenses/by/2.1/jp/" target="_blank" rel="noopener noreferrer">https://creativecommons.org/licenses/by/2.1/jp/</a>）</p>
"""
soup.body.append(BeautifulSoup(text, 'html.parser'))

with open(OUTPUT_HTML, 'w', encoding='utf-8') as file:
  # minifyとかしたほうがいいのかなと思ったけど今は保留
  file.write(str(soup))
