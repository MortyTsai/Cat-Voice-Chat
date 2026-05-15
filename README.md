# Local AI Cat Voice Assistant

這是一個結合了本地 LLM 與 TTS 技術的 AI 語音助手實作專案。本專案旨在練習打造一個說話帶有「喵」口頭禪、且能實現極低延遲、無感裁切的流式語音對話系統。

## 📖 學習歷程 (Learning Journey)

本專案是在 AI 助手的全面支持下完成的 **「AI 協作開發 (AI-Augmented Development)」** 練習。我將其定義為一次從零開始的系統整合挑戰，目標是打通從文字生成 $\rightarrow$ 音訊合成 $\rightarrow$ 物理硬體輸出這條複雜的管線。

在開發過程中，我並不追求一次成功的程式碼，而是採取 **「診斷 $\rightarrow$ 測試 $\rightarrow$ 修正」** 的迭代路徑。透過這次實作，我深入理解了 Windows 音訊驅動的底層行為、API 串流的同步問題以及 AI 模型的 lToken 處理特性。

### 技術棧 (Tech Stack)
- **LLM 引擎**: [Ollama](https://ollama.com/) (基於 Gemma 4 微調的 `my_cat:latest`)
- **TTS 引擎**: [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) (API Mode)
- **音訊處理**: `sounddevice` (直接驅動 PortAudio), `pydub` (音訊操作), `numpy` (數值計算)
- **語言**: Python 3.10+

---

## 實作中的挑戰

這是我在開發過程中遇到的核心挑戰，以及如何一步步解決它們的紀錄：

### 1. 文本前端與「吞音」現象
- **問題**：發現句尾的 `，喵~` 經常被 TTS 吞掉而不發音，但 `喵~喵~` 或 `測試語音喵~` 則正常。
- **分析**：GPT-SoVITS 在處理標點符號後，若單個片段僅剩一個字，模型容易將其發音長度預測為 0。
- **解決方案**：使用正則表達式 $\text{Regex}$ 移除「喵」之前的標點，將其與前句「黏合」，強制模型將其視為同一語塊。

### 2. 「起音裁切 (Initial Clipping)」
- **問題**：每個句子的第一個字總是感覺被切掉了一小部分。
- **探索路徑 (失敗 $\rightarrow$ 成功)**：
    1. $\text{ffplay 濾鏡 (adelay)}$ $\rightarrow$ 無效。
    2. $\text{物理靜音填充}$ $\rightarrow$ 發現音效卡驅動具有 **「自動門 (Audio Gating)」** 機制，純靜音無法喚醒硬體。
    3. $\text{sounddevice 直接播放}$ $\rightarrow$ 減少進程啟動延遲，但依然存在驅動握手時間。
- **最終突破**：實作 **「恆定流 (Constant Stream)」** 機制。建立一個永不停止的 `OutputStream`，並持續輸出極低電平的隨機噪音（Comfort Noise）作為心跳信號，欺騙驅動程式讓其保持喚醒狀態，徹底消除裁切感。

### 3. 長文推理超時與維度衝突
- **問題**：生成長故事時觸發 `Read timed out`；且在實現恆定流時出現 `ValueError` 維度不匹配。
- **解決方案**：
    - **斷句策略**：實作 `split_text` 邏輯，將長文按標點切分為小句循序生成，既解決了超時問題，也降低了使用者的體感延遲。
    - **維度對齊**：將隨機噪音陣列形狀明確指定為 `(frames, 1)` 以對接 `outdata` 的二維結構。

---

## 環境準備 (Prerequisites)

本專案為 API 呼叫端，需在本地端啟動 LLM 與 TTS 伺服器。

### 1. LLM 伺服器 (Ollama)
- 安裝 [Ollama](https://ollama.com/)。
- **模型獲取**：
  - 本專案使用微調後的 Gemma 4 模型，權重已上傳至 Hugging Face：上傳中。
  - **匯入 Ollama**：
    1. 下載 `.gguf` 檔案到本地。
    2. 建立 `Modelfile` 並指定 `FROM ./your-model.gguf` 以及適當的 `SYSTEM` Prompt。
    3. 執行 `ollama create my_cat -f Modelfile`。

### 2. TTS 伺服器 (GPT-SoVITS)
- **下載整合包**：前往 [GPT-SoVITS 官方 GitHub](https://github.com/RVC-Boss/GPT-SoVITS) 下載 Windows 整合包。
- **啟動 API**：進入整合包目錄，執行 `api_v2.py`：
  ```powershell
  .\runtime\python.exe api_v2.py -a 127.0.0.1 -p 9880
  ```
- **參考音訊**：請準備一個 3~10 秒的 `.wav` 參考音訊，並在 `main.py` 的 `TTS_PARAMS` 中填入路徑。

---

## 執行步驟

1. **安裝 Python 依賴**：
   ```bash
   pip install -r requirements.txt
   ```

2. **啟動伺服器**：
   - 啟動 Ollama $\rightarrow$ 載入 `my_cat:latest`。
   - 啟動 GPT-SoVITS API $\rightarrow$ 確認 `http://127.0.0.1:9880` 可訪問。

3. **執行助手**：
   ```bash
   python main.py
   ```

## 結語
這次練習讓我意識到，AI 應用開發中最困難的往往不是模型本身，而是 AI 與物理硬體之間的「最後一哩路」。透過與 AI 的協作，我學習到如何從現象分析底層原因，並用工程手段（恆定流、斷句、噪音填充）來克服硬體限制。

---
**License**: [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) (Following Gemma Base Model License)
