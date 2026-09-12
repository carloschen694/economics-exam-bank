# ANTIGRAVITY.md - 專案規範與引導

## 專案基本資訊
- **專案名稱**：經濟學研究所考試題庫 & 經濟學考試練習 (economics-exam-bank)
- **專案類型**：API 後端服務 (Backend API Service)
- **核心目標**：
  1. 提供經濟學研究所入學考試（個體經濟學、總體經濟學、統計學與計量經濟學）考古題題庫儲存、檢索與分類。
  2. 提供線上練習、題組測驗、詳解與答題紀錄之後端 API 介面。
- **儲存庫**：https://github.com/carloschen694/economics-exam-bank (Public)
- **部署狀態**：暫不部署（本機開發階段）

---

## AntiGravity 工作流程規範

### 1. 開工流程 (Start of Work)
1. 讀取本檔案 (`ANTIGRAVITY.md`) 與相關架構設計。
2. 讀取 Obsidian 專案筆記中的待辦清單與進度。
3. 執行 `git status` 與確認最近的 commit 狀態。
4. 回報當前工作狀態與建議的下一步工作。
5. **不自動執行 pull / commit / push**。

### 2. 收工流程 (End of Work)
1. 檢查敏感資料：確保任何 API Key、Token、資料庫連線字串或個人識別資訊未被寫死在程式碼中。
2. 更新專案筆記：記錄本次完成事項、踩坑經驗與下一步規劃。
3. 僅在專案規則或架構有所更動時，同步更新本 `ANTIGRAVITY.md`。
4. 檢查 `git status` 與 `git diff`。
5. 明確 stage 本次變更檔案（**嚴禁使用 `git add .`**）。
6. 徵詢確認後進行 commit 與 push。
7. 回報同步結果。

---

## 開發守則與規範
- **安全性**：環境變數一律由 `.env` 管理，且 `.env` 必須列入 `.gitignore`。
- **架構原則**：模組化分層設計（API 路由、服務邏輯層、資料存取層、資料模型）。
- **文件維護**：新增或修改 API 端點時，同步維護 API Spec 文件或 OpenAPI / Swagger 說明。
