import requests
import re
import sys
import io
import numpy as np
import sounddevice as sd
from pydub import AudioSegment
from collections import deque

# ================= 配置區塊 =================
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "my_cat:latest"
GPT_SOVITS_API_URL = "http://127.0.0.1:9880/tts"

TTS_PARAMS = {
    "text_lang": "zh",
    "prompt_lang": "zh",
    "prompt_text": "", # 替換為你的參考音訊文字
    "ref_audio_path": "", # 替換為你的參考音訊路徑
    "top_k": 15,
    "top_p": 0.85,
    "temperature": 0.8,
    "media_type": "wav",
    "streaming_mode": False
}
# ============================================

class StreamPlayer:
    def __init__(self):
        # 使用 deque 儲存所有採樣點，實現真正的流式播放
        self.buffer = deque()
        self.sample_rate = 32000 
        
        # 啟動背景播放線程
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1, 
            callback=self._callback
        )
        self.stream.start()

    def _callback(self, outdata, frames, time, status):
        """回調函數：精確填充音效卡緩衝區"""
        if status:
            print(f"Stream Status: {status}", file=sys.stderr)
        
        # 嘗試從 buffer 中取出所需數量的採樣點
        count = 0
        while count < frames and self.buffer:
            outdata[count, 0] = self.buffer.popleft()
            count += 1
        
        # 如果 buffer 沒東西了，用極微小噪音填充剩餘空間，防止驅動關門 (修正維度問題)
        if count < frames:
            noise = np.random.uniform(-0.0002, 0.0002, size=(frames - count, 1)).astype(np.float32)
            outdata[count:] = noise

    def play_audio(self, audio_bytes):
        """將音訊轉換為採樣點流並推入 buffer"""
        try:
            sound = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
            sound = sound.set_channels(1).set_frame_rate(self.sample_rate)
            
            samples = np.array(sound.get_array_of_samples()).astype(np.float32)
            samples /= (2**15) if sound.sample_width == 2 else (2**7)
            
            # 將所有採樣點逐個加入 deque
            self.buffer.extend(samples)
        except Exception as e:
            print(f"\n[音訊轉換錯誤] {e}")

    def stop(self):
        self.stream.stop()
        self.stream.close()

class CatAssistant:
    def __init__(self):
        self.player = StreamPlayer()

    def split_text(self, text):
        sentences = re.split(r'([。！？\n,，])', text)
        result = []
        for i in range(0, len(sentences)-1, 2):
            result.append(sentences[i] + sentences[i+1])
        if len(sentences) % 2 == 1:
            result.append(sentences[-1])
        return [s.strip() for s in result if s.strip()]

    def process_text_for_tts(self, text):
        processed_text = re.sub(r'[，,。！!？\?]\s*(喵)', r'\1', text)
        processed_text = re.sub(r'喵+', '喵~', processed_text)
        return processed_text

    def get_llm_response(self, prompt):
        payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
        try:
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
            response.raise_for_status()
            return response.json().get("response", "").replace("<|turn>model", "").strip()
        except Exception as e:
            print(f"\n[LLM 錯誤] {e}")
            return None

    def generate_and_play_audio(self, full_text):
        sentences = self.split_text(full_text)
        for sentence in sentences:
            processed_text = self.process_text_for_tts(sentence)
            payload = TTS_PARAMS.copy()
            payload["text"] = processed_text
            try:
                response = requests.post(GPT_SOVITS_API_URL, json=payload, timeout=60)
                response.raise_for_status()
                self.player.play_audio(response.content)
            except Exception as e:
                print(f"\n[TTS 錯誤] {e}")

    def chat_loop(self):
        print("="*50)
        print("🐱 貓咪語音助手 已啟動！")
        print("="*50)
        while True:
            try:
                user_input = input("\n你: ").strip()
                if user_input.lower() in ['exit', 'quit']: break
                if not user_input: continue
                print("貓咪思考中...", end="\r")
                reply = self.get_llm_response(user_input)
                if reply:
                    sys.stdout.write("\033[K") 
                    print(f"貓咪: {reply}")
                    self.generate_and_play_audio(reply)
            except KeyboardInterrupt: break
        self.player.stop()

if __name__ == "__main__":
    assistant = CatAssistant()
    assistant.chat_loop()
