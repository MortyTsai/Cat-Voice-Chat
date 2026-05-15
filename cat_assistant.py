import asyncio
import subprocess
import re
import random
import ollama
from edge_tts import Communicate

# ================= 配置區 =================
MODEL_NAME = "my_cat:latest"
VOICE = "zh-CN-XiaoxiaoNeural" 

VOICE_PITCH = "+25Hz" 
VOICE_RATE = "+12%"   

MEOW_VARIANTS = ["，喵～", "，喵～～", "，喵！", "...喵～", " 喵～"]
# =========================================

class OllamaClient:
    def __init__(self, model):
        self.model = model

    def clean_response(self, text):
        text = re.sub(r'<\|[^>\n]*>?', '', text)
        role_pattern = r'^(user|model|assistant|human|主人|貓咪):\s*'
        text = re.sub(role_pattern, '', text, flags=re.MULTILINE)
        return text.strip()

    async def chat(self, prompt):
        try:
            response = ollama.chat(
                model=self.model, 
                messages=[{'role': 'user', 'content': prompt}],
                options={"stop": ["<|turn>", "<|end_of_turn>", "user:"]}
            )
            return self.clean_response(response['message']['content'])
        except Exception as e:
            return f"【系統錯誤】喵...我的大腦好像短路了：{str(e)}"

class TTSPlayer:
    def __init__(self, voice):
        self.voice = voice

    def enhance_prosody(self, text):
        """
        韻律增強器：將標準文本轉換為具有情感起伏的口語文本
        """
        # 1. 隨機注入句首語助詞
        fillers = ["嗯... ", "嘿嘿，", "那個... ", "唔... ", ""]
        if random.random() < 0.3: # 30% 機率加入
            text = random.choice(fillers) + text

        # 2. 標點符號情感化
        text = text.replace("。", "～")
        text = text.replace("！", "～～")
        
        # 3. 模擬呼吸停頓
        if len(text) > 15:
            parts = text.split('，')
            if len(parts) > 1:
                # 隨機將其中一個逗號替換為省略號
                idx = random.randint(0, len(parts)-1)
                parts[idx] = parts[idx] + "..."
                text = "，".join(parts)

        # 4. 喵的動態處理
        if "喵" in text:
            text = re.sub(r'(喵)[～！\s]*$', random.choice(MEOW_VARIANTS), text)
            text = re.sub(r'([，。！？])喵', r'\1' + random.choice(MEOW_VARIANTS), text)
        else:
            text += random.choice(MEOW_VARIANTS)

        return text

    async def play_text(self, text):
        processed_text = self.enhance_prosody(text)
        
        # 打印出處理後的文本，方便你觀察 TTS 實際上在讀什麼
        print(f"  [TTS 讀取內容]: {processed_text}")

        communicate = Communicate(
            processed_text, 
            self.voice, 
            pitch=VOICE_PITCH, 
            rate=VOICE_RATE
        )
        
        player_proc = subprocess.Popen(
            ['ffplay', '-nodisp', '-autoexit', '-f', 'mp3', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    player_proc.stdin.write(chunk["data"])
        except Exception as e:
            print(f"播放錯誤: {e}")
        finally:
            if player_proc.stdin:
                player_proc.stdin.close()
            player_proc.wait()

class CatAssistant:
    def __init__(self):
        self.llm = OllamaClient(MODEL_NAME)
        self.tts = TTSPlayer(VOICE)

    async def run(self):
        print("🐱 貓咪助手 (情感增強版) 已上線！")
        print("-" * 30)
        
        while True:
            try:
                user_input = input("主人: ")
                if user_input.lower() in ['exit', 'quit', '再見']:
                    print("貓咪: 掰掰喵～～ 🐾")
                    break
                if not user_input.strip(): continue

                print("貓咪思考中...", end="\r")
                response_text = await self.llm.chat(user_input)
                print(f"貓咪: {response_text}")

                await self.tts.play_text(response_text)
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    assistant = CatAssistant()
    try:
        asyncio.run(assistant.run())
    except KeyboardInterrupt:
        print("\n程式已強制停止喵！")
