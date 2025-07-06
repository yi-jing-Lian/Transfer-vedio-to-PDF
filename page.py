import pyautogui
import time

# 點擊位置（X, Y），你要先用螢幕截圖工具或 pyautogui.position() 得到按鈕座標
click_x = 1907
click_y = 589

# 點擊間隔秒數（翻頁速度）
interval = 5

# 翻頁次數
page_count = 150

print("5秒後開始自動點擊，請切換到你的電子書視窗...")
time.sleep(5)

for i in range(page_count):
    pyautogui.click(click_x, click_y)
    time.sleep(interval)
