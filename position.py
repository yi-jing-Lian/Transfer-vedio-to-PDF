import pyautogui,time
print("請移動滑鼠到目標位置，3秒後開始讀取座標...")
time.sleep(10)
print(pyautogui.position())
