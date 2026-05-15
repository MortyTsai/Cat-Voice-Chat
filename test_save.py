import requests

# 請確保這裡的設定跟你的 main.py 一模一樣
payload = {
    "text_lang": "zh",
    "prompt_lang": "zh",
    "prompt_text": "大家好，我是宁宁。我中文还不是很熟练，但是希望大家能喜欢我的声音，喵喵喵！", # 替換為你的參考音訊文字
    "ref_audio_path": "D:/Python/CatVoiceAssistant/my_voice/tmpo1ftlmcz.wav", # 替換為你的參考音訊路徑
    "text": "這是一句測試語音，喵~",
    "media_type": "wav",       # 測試時改回 wav
    "streaming_mode": False    # 關閉串流，讓伺服器整句生成完再傳過來
}

print("正在生成語音並存檔...")
response = requests.post("http://127.0.0.1:9880/tts", json=payload)

if response.status_code == 200:
    with open("test_output.wav", "wb") as f:
        f.write(response.content)
    print("✅ 成功！已儲存為 test_output.wav")
    print("👉 請去資料夾點擊 test_output.wav，用 Windows 內建的播放器聽聽看！")
else:
    print(f"錯誤: {response.status_code}")