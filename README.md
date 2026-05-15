# Local AI Cat Voice Assistant

這是一個結合了本地 LLM 與 TTS 技術的 AI 語音助手實作專案。本專案旨在打造一個說話帶有「喵」口頭禪、且能實現極低延遲、無感裁切的流式語音對話系統。

## 📖 學習歷程 (Learning Journey)

本專案是在 AI 助手的全面支持下完成的 **「AI 協作開發 (AI-Augmented Development)」** 練習。我將其定義為一次從零開始的系統整合挑戰，目標是打通從文字生成 $\rightarrow$ 音訊合成 $\rightarrow$ 物理硬體輸出這條複雜的管線。

在開發過程中，我採取 **「診斷 $\rightarrow$ 測試 $\rightarrow$ 修正」** 的迭代路徑。透過這次實作，我深入理解了 Windows 音訊驅動的底層行為、API 串流的同步問題以及 AI 模型的 Token 處理特性。

---

## 環境配置與準備 (Prerequisites)

### 1. Python 虛擬環境配置
為了避免套件衝突，請務必使用虛擬環境：
```powershell
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境 (Windows)
.\venv\Scripts\activate

# 安裝必要依賴
pip install -r requirements.txt
```

### 2. LLM 伺服器 (Ollama) 匯入流程
本專案使用微調後的 Gemma 4 模型。取得 `.gguf` 權重檔案後，請依照以下步驟匯入 Ollama：
1. 在模型檔案同目錄下建立一個名為 `Modelfile` 的文字檔，內容如下：
   ```dockerfile
   # 載入大腦
   FROM ./gemma-4-e4b-it.Q4_K_M.gguf
   # 這會告訴模型：你可以思考，但請不要把思考過程寫出來，直接給我答案。
   SYSTEM """You are a helpful assistant. Please perform your reasoning internally and output only the final response to the user. Do not include 'Thinking Process' or 'Thinking...' in your output. Remember to always end your sentences with your catchphrase '喵！'"""
   # 設定對話模板
   TEMPLATE """<bos><|turn>user
   {{ .Prompt }}<turn|>
   <|turn>model
   """
   # 設定停止標記
   PARAMETER stop "<turn|>"
   PARAMETER temperature 0.7
   PARAMETER top_p 0.95
   ```
2. 開啟終端機執行指令建立模型：
   ```powershell
   ollama create my_cat -f Modelfile
   ```
3. 確保模型已成功運行：`ollama run my_cat`

### 3. TTS 伺服器 (GPT-SoVITS)
- **下載整合包**：前往 [GPT-SoVITS 官方 GitHub](https://github.com/RVC-Boss/GPT-SoVITS) 下載 Windows 整合包。
- **啟動 API**：進入整合包目錄，執行 `api_v2.py`：
  ```powershell
  .\runtime\python.exe api_v2.py -a 127.0.0.1 -p 9880
  ```

---

## 極重要：音訊配置指南 (Critical Warning)

GPT-SoVITS 是基於參考音訊進行克隆的。在 `main.py` 或 `test_save.py` 的 `TTS_PARAMS` 中：

**`refer_wav_path` (參考音訊) 與 `prompt_text` (參考文字) 必須完全適配！**

- **適配定義**：`prompt_text` 必須是你提供的 `.wav` 檔案中**實際說出的文字**。
- **後果**：如果文字與音訊內容不符，模型將無法正確提取音色特徵，導致輸出語音出現嚴重的雜音、電音或無法正常發聲。
- **音訊獲取**：本專案不提供參考音訊。建議前往 [Hugging Face](https://huggingface.co/) 搜尋 `GPT-SoVITS` 相關資料集，或使用錄音軟體錄製一段 3~10 秒乾淨且語氣輕快的 `.wav` 檔案。

---

## 執行方案

### 方案 A：快速體驗 (僅測試 TTS)
如果你還沒有配置好 Ollama 或不想下載大型權重，可以使用 `test_save.py` 來驗證 TTS 伺服器是否運作正常。
- **功能**：將一句測試文字傳給伺服器，並儲存為 `test_output.wav`。
- **執行**：
  ```bash
  python test_save.py
  ```

### 方案 B：完整對話體驗 (LLM + TTS)
啟動所有伺服器後，執行主程式開啟對話迴圈。
- **執行**：
  ```bash
  python main.py
  ```

---

## 🛠️ 技術突破紀錄 (Technical Log)

這是我在開發過程中遇到的核心挑戰，以及如何一步步解決它們的紀錄：

### 1. 文本前端與「吞音」現象
- **問題**：發現句尾的 `，喵~` 經常被 TTS 吞掉而不發音。
- **解決方案**：使用正則表達式 $\text{Regex}$ 移除「喵」之前的標點，將其與前句「黏合」。

### 2. 噩夢般的「起音裁切 (Initial Clipping)」
- **問題**：每個句子的第一個字總是感覺被切掉了一小部分。
- **探索路徑**：$\text{ffplay 濾鏡}$ $\rightarrow$ $\text{物理靜音填充}$ $\rightarrow$ $\text{sounddevice 直接播放}$ $\rightarrow$ **發現音效卡「自動門 (Audio Gating)」機制**。
- **最終突破**：實作 **「恆定流 (Constant Stream)」** 機制。建立一個永不停止的 `OutputStream`，並持續輸出極低電平的隨機噪音（Comfort Noise）作為心跳信號，強迫音效卡保持喚醒狀態。

### 3. 長文推理超時與維度衝突
- **問題**：長文生成觸發 `Read timed out`；恆定流實作時出現 NumPy `ValueError`。
- **解決方案**：
    - **斷句策略**：實作 `split_text` 將長文切分小句循序播放，降低體感延遲並解決超時。
    - **維度對齊**：將噪音陣列形狀明確指定為 `(frames, 1)` 以對接 `outdata` 結構。

---

## 結語
這次練習讓我意識到，AI 應用開發中最困難的往往不是模型本身，而是 AI 與物理硬體之間的「最後一哩路」。透過與 AI 的協作，我學習到如何從現象分析底層原因，並用工程手段來克服硬體限制。

---
**License**: [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) (Following Gemma Base Model License)
