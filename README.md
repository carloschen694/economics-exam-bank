# 經濟學研究所考試題庫 & 經濟學考試練習 API (economics-exam-bank)

專為準備台灣與海外經濟學研究所（個體經濟學、總體經濟學、統計學 / 計量經濟學）考生設計的考古題庫與測驗練習後端 API 服務。

---

## 🎯 核心功能願景

- **考古題庫管理與檢索**：
  - 支援按學校（台大、政大、清大、交大等）、系所、考試年度、考科（個體、總體、統計）分類檢索。
  - 支援題型篩選（選擇題、簡答計算題、證明題、申論分析題）。
  - 支援標籤機制（如：Solow 模型、賽局理論、IS-LM/AD-AS、OLS 回歸性質、Nash 均衡等主題標籤）。
- **考試測驗與練習模組**：
  - 隨機抽題測驗 / 歷屆整份模擬考試。
  - 答題紀錄追蹤與統計（正確率、作答時間、薄弱題型分析）。
  - 詳解與評分標準提供。
- **題庫維護與匯入 API**：
  - 支援批次題目匯入（JSON / Markdown / LaTeX 數學公式格式）。

---

## 🏗️ 規劃 API 端點結構 (預覽)

- `GET /api/v1/exams` - 查詢歷屆試卷列表
- `GET /api/v1/exams/{id}` - 取得特定試卷完整題目
- `GET /api/v1/questions` - 條件篩選檢索題目（學校、年份、主題標籤）
- `GET /api/v1/questions/{id}` - 取得題目詳情與解答
- `POST /api/v1/practice/submit` - 提交練習作答並批改回傳解析
- `GET /api/v1/stats/summary` - 獲取複習數據與弱點分佈

---

## 🛠️ 技術棧建議

- 後端框架：建議使用 Python (FastAPI) 或 Node.js / TypeScript
- 資料儲存：PostgreSQL / SQLite（開發環境）
- 文件支援：LaTeX 數學公式輸出支援 (MathJax / KaTeX 格式)

---

## 🚀 快速開始

### 1. 安裝相依套件（後續依選擇之框架建立）
```bash
# 待專案依賴建立後更新
```

### 2. 環境變數設定
複製 `.env.example` 並設定對應參數：
```bash
cp .env.example .env
```

---

## 📄 授權條款
MIT License
