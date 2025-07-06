import os
import subprocess
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from PIL import Image

VIDEO_FILE = "2025-07-06 19-16-41.mp4"
AUDIO_FILE = "audio.wav"
IMG_FOLDER = "images"
IMG_PREFIX = "img"
OUTPUT_PDF = "output.pdf"

def extract_audio(video_file, audio_file):
    """ 從影片擷取音訊 """
    cmd = ["ffmpeg", "-y", "-i", video_file, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", audio_file]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def detect_click_times(audio_path, min_silence_len=200, silence_thresh=-40):
    """
    使用 pydub 找出音訊中非靜默片段 (即有聲音部分)，
    假設翻頁聲是明顯聲響，回傳這些段落的開始時間（秒）
    """
    audio = AudioSegment.from_wav(audio_path)
    nonsilent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    # nonsilent_ranges = [(start_ms, end_ms), ...]
    # 取每段非靜默起始時間（秒）
    times = [start / 1000.0 for start, end in nonsilent_ranges]
    return times

def filter_final_clicks(time_stamps, delta=1.0):
    """
    過濾連續時間點，只保留每組最後一個時間點
    """
    if not time_stamps:
        return []

    filtered = []
    group = [time_stamps[0]]

    for current in time_stamps[1:]:
        if current - group[-1] <= delta:
            group.append(current)
        else:
            filtered.append(group[-1])
            group = [current]

    filtered.append(group[-1])
    return filtered

def extract_images(time_stamps, max_retries=10, delay_step=0.1, pre_offset=0.6):
    print("🖼️ 擷取圖片中...")

    if not os.path.exists(IMG_FOLDER):
        os.makedirs(IMG_FOLDER)
    else:
        # 清空舊圖片
        for f in os.listdir(IMG_FOLDER):
            if f.endswith(".png"):
                os.remove(os.path.join(IMG_FOLDER, f))

    for idx, t in enumerate(time_stamps):
        success = False
        for retry in range(max_retries):
            adjusted_t = max(0, round(t - pre_offset + retry * delay_step, 2))
            out_img = f"{IMG_FOLDER}/{IMG_PREFIX}{idx+1:04d}.png"

            cmd = [
                "ffmpeg", "-ss", str(adjusted_t), "-i", VIDEO_FILE,
                "-frames:v", "1", "-q:v", "2", out_img, "-y"
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if os.path.exists(out_img):
                print(f"✅ 擷取成功（時間點 {adjusted_t} 秒）：{out_img}")
                success = True
                break

        if not success:
            print(f"❌ 擷取失敗（原始時間點 {t} 秒）：{out_img}")

    # 擷取最後翻頁聲後的下一頁畫面（多抓最後一張）
    if time_stamps:
        last_time = time_stamps[-1]
        last_page_time = last_time + 1.0  # 你可以調整這個秒數
        out_img = f"{IMG_FOLDER}/{IMG_PREFIX}{len(time_stamps)+1:04d}.png"

        success = False
        for retry in range(max_retries):
            adjusted_t = max(0, round(last_page_time - pre_offset + retry * delay_step, 2))

            cmd = [
                "ffmpeg", "-ss", str(adjusted_t), "-i", VIDEO_FILE,
                "-frames:v", "1", "-q:v", "2", out_img, "-y"
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if os.path.exists(out_img):
                print(f"✅ 擷取最後一頁成功（時間點 {adjusted_t} 秒）：{out_img}")
                success = True
                break

        if not success:
            print(f"❌ 擷取最後一頁失敗（原始時間點 {last_page_time} 秒）：{out_img}")


def images_to_pdf(img_folder, output_pdf):
    imgs = []
    files = sorted([f for f in os.listdir(img_folder) if f.endswith(".png")])
    for f in files:
        img_path = os.path.join(img_folder, f)
        img = Image.open(img_path).convert("RGB")
        imgs.append(img)
    if imgs:
        imgs[0].save(output_pdf, save_all=True, append_images=imgs[1:])
        print(f"✅ PDF 已儲存為：{output_pdf}")
    else:
        print("⚠️ 沒有圖片可轉成 PDF")

def main():
    print("🎬 從影片擷取音訊...")
    extract_audio(VIDEO_FILE, AUDIO_FILE)

    print("🔊 偵測翻頁聲音時間點...")
    raw_times = detect_click_times(AUDIO_FILE)

    print(f"✅ 原始偵測到 {len(raw_times)} 個翻頁聲")

    filtered_times = filter_final_clicks(raw_times, delta=1.0)
    print(f"✅ 過濾後剩 {len(filtered_times)} 個翻頁時間點")
    for i, t in enumerate(filtered_times, 1):
        print(f" - 第 {i} 頁：{round(t, 2)} 秒")

    extract_images(filtered_times)

    print("📄 轉換為 PDF 中...")
    images_to_pdf(IMG_FOLDER, OUTPUT_PDF)

if __name__ == "__main__":
    main()
