# Local AI Cat Voice Assistant

這是一個結合了本地 LLM 與 TTS 技術的 AI 語音助手實作練習。本專案旨在嘗試打造一個說話帶有「喵」口頭禪、並盡量降低延遲且優化語音裁切感的流式對話系統。

---

## 🛑 免責聲明 / Disclaimer

### 中文
本專案（Cat-Voice-Chat）僅供個人學習、學術研究與技術交流使用。請勿將本專案中所涉及的語音合成、聲音複製等技術用於任何非法用途（如詐騙、偽造身分、名譽毀損等）。

本專案作者不對任何人因惡意使用、不當操作或傳播此技術與模型所造成的任何直接或間接損失負責。下載、複製或使用本專案代碼與模型權重即代表您同意本聲明。

---

## 📖 學習歷程 (Learning Journey)

本專案是在 AI 助手的支持下完成的 **「AI 協作開發 (AI-Augmented Development)」** 練習。對我而言，這是一次嘗試將文字生成 $\rightarrow$ 音訊合成 $\rightarrow$ 物理硬體輸出這條管線串接起來的系統整合練習。

在開發過程中，我採取 **「觀察 $\rightarrow$ 測試 $\rightarrow$ 調整」** 的迭代路徑。透過這次實作，我對 Windows 音訊驅動的行為、API 串流的同步問題以及 AI 模型的 Token 處理特性有了初步的認識。

---

## 環境配置與準備 (Prerequisites)

### 1. Python 虛擬環境配置
為了避免套件衝突，建議使用虛擬環境：
```powershell
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境 (Windows)
.\venv\Scripts\activate

# 安裝必要依賴
pip install -r requirements.txt
```

### 2. LLM 伺服器 (Ollama) 與模型匯入

本專案使用微調後的 Gemma 4 模型。您可以選擇自行微調，或是下載我分享的權重檔案。

🚀 **微調模型權重下載：[上傳中](https://www.google.com/url?sa=E&source=gmail&q=https://huggingface.co/MortyTsai/my_cat)**

取得 `.gguf` 權重檔案後，請依照以下步驟匯入 Ollama：

1. 在模型檔案同目錄下建立一個名為 `Modelfile` 的文字檔，內容如下：
```dockerfile
# 載入模型
FROM ./gemma-4-e4b-it.Q4_K_M.gguf
# 設定系統提示詞：要求模型內部思考，僅輸出最終答案，並在句尾加上口頭禪
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

3. 確認模型可正常運行：`ollama run my_cat`

### 3. TTS 伺服器 (GPT-SoVITS)

* **下載整合包**：請前往 [GPT-SoVITS 官方 GitHub](https://github.com/RVC-Boss/GPT-SoVITS) 下載 Windows 整合包。
* **啟動 API**：進入整合包目錄，執行 `api_v2.py`：
```powershell
.\runtime\python.exe api_v2.py -a 127.0.0.1 -p 9880
```

---

## ⚠️ 重要：音訊配置指南 (Critical Warning)

GPT-SoVITS 是基於參考音訊進行克隆的。在 `main.py` 或 `test_save.py` 的 `TTS_PARAMS` 中：

**`refer_wav_path` (參考音訊) 與 `prompt_text` (參考文字) 必須完全適配！**

* **適配定義**：`prompt_text` 必須是您提供的 `.wav` 檔案中**實際說出的文字**。
* **影響**：如果文字與音訊內容不符，模型可能無法正確提取音色特徵，導致輸出語音出現雜音或發聲異常。
* **音訊獲取**：本專案不提供預設的參考音訊。建議前往 Hugging Face 搜尋 `GPT-SoVITS` 相關公開資料集，或自行錄製一段 3~10 秒乾淨且語氣輕快的 `.wav` 檔案作為參考。

---

## 執行方案

### 方案 A：快速體驗 (僅測試 TTS)

如果您尚未配置 Ollama，可以使用 `test_save.py` 來驗證 TTS 伺服器是否運作正常。

* **功能**：將測試文字傳給伺服器，並儲存為 `test_output.wav`。
* **執行**：
```bash
python test_save.py
```

### 方案 B：完整對話體驗 (LLM + TTS)

啟動所有伺服器後，執行主程式開啟對話迴圈。

* **執行**：
```bash
python main.py
```

---

## 🛠️ 開發過程中的調整紀錄 (Technical Log)

在開發過程中遇到了一些問題，以下是我嘗試調整並改善的紀錄：

### 1. 文本前端與「吞音」現象
* **觀察**：發現句尾的 `，喵~` 在某些情況下會被 TTS 忽略而不發音。
* **嘗試調整**：使用正則表達式 $\text{Regex}$ 移除「喵」之前的標點符號，嘗試將其與前句「黏合」，以改善發音的連貫性。

### 2. 關於「起音裁切 (Initial Clipping)」的嘗試
* **觀察**：每個句子的第一個字有時會感覺被切掉了一小部分。
* **探索路徑**：嘗試過 $\text{ffplay 濾鏡}$ $\rightarrow$ $\text{物理靜音填充}$ $\rightarrow$ $\text{sounddevice 直接播放}$，進而了解到音效卡可能存在「自動門 (Audio Gating)」機制。
* **目前的處理方式**：實作了一套簡單的 **「恆定流 (Constant Stream)」** 機制。建立一個持續運行的 `OutputStream`，並輸出極低電平的隨機噪音（Comfort Noise）作為心跳信號，嘗試讓音效卡保持在喚醒狀態以減少裁切感。

### 3. 長文推理超時與維度衝突
* **觀察**：生成較長文本時偶爾會觸發 `Read timed out`；在實作恆定流時出現 NumPy `ValueError`。
* **調整方向**：
    * **斷句策略**：實作 `split_text` 將長文切分為小句循序播放，嘗試降低體感延遲並避免超時。
    * **維度對齊**：將噪音陣列形狀明確指定為 `(frames, 1)`，以符合 `outdata` 的結構要求。

---

**License**: [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) (Following Gemma Base Model License)
