---
name: assign-writing-task
description: 通用「writer → checker → reviewer → 主 agent 決策」 subagent 流程。當各階段 skill 需要把「寫」與「審」分離、或需建立可重做的 subagent 迴圈時，由該階段 skill 引用本檔。
---

# 寫稿／符合性檢查／品質審查 protocol（通用）

## 目的
在本專案中需要寫稿與需要審查時就會利用此 skill 同一完成任務。

## 角色分工

| 角色            | 誰擔任                                               | 職責                           |
| ------------- | ------------------------------------------------- | -------------------------------- |
| **寫稿 worker** | `writer` subagent（`.agents/agents/writer.md`）     | 依階段任務規格產出稿件                      | 
| **審查 worker** | `checker` 與 `reviewer` subagent（`.agents/agents/`） | checker 對照故事文件及硬性規範；reviewer 評可聽性並給修正方向         |
| **主 agent**   | 當前 session                                        | 派發、讀稿＋審查意見、產 handoff/report、決策退回 |
### 流程與輸入輸出

1. 主 agent 將任務說明、故事文件、寫作指引及必要的前稿／交接資料交 writer，取得章節稿件。
2. 將稿件、故事文件、已接受的前章及明確規範交 checker，取得符合性 JSON。
3. 將稿件、必要前後章、品質標準及作者偏好交 reviewer，取得獨立的品質 JSON；reviewer 不讀 checker 的判定。
4. 主 agent 讀兩份結果，決定收下、退回 writer 或交人類確認。退回時只交相關問題及採納的修正方向。
5. 全章完成後，主 agent 彙整 `report.md`、`handoff.md` 及下一輪修改說明。

checker 未通過時由主 agent 決定是否先退回；若尚未退回，reviewer 仍獨立審讀。兩者均不得自行改稿或決定退回。

## 模型選擇
模型選擇會寫在 **任務說明** 之中，如果沒有寫的話，則預設使用下面的規則

| 角色            | 草稿                          | 其他狀況                           |
| ------------- | ------------------------------ | ------------------------------ |
| **寫稿 worker** | deepseek-V4-flash   | deepseek-V4-flash |
| **checker** | GLM-5.2   | GLM-5.2 |
| **reviewer** | GPT-6-Sol   | GPT-6-Sol |
| **主 agent**   | GPT-6-Sol  | GPT-6-Sol  |

## 執行步驟

逐章依上方流程執行。若 writer 修稿，主 agent 重新派發受修改影響的 checker／reviewer 檢查；兩份結果及退回次數均保留。全篇草稿完成後，checker 另核對跨章設定與結局，reviewer 可回報跨章品質問題，主 agent 再決定本 loop 結果。

人類在 loop 結束時覆核，下一 loop 依其意見與主 agent 採納的審查意見進行。模型選擇與 loop 次數沿用階段任務設定。

## 檔案標準

* checker 參考 `specs/standards/草稿總審查標準.md` 的故事文件項目及 `specs/standards/草稿撰寫審查標準.md` 的硬性格式項目；reviewer 參考後者的品質項目與前者的商業品質四軸 
* reviewer 逐句驗證因果與主詞時，依 `punchline-first-review` skill（Read `.agents/skills/punchline-first-review.md`）的流程執行：先認定每句的 punch line 落點，再驗證支撐鏈
- 主 agent 寫 handoff 時參考 `handoff` SKILL

### report.md — 給人類與歸檔的完整紀錄

路徑：`{work_dir}/report.md`

```markdown
# {階段} 審查報告 — {作品名} — {date}

## 各章結果總表
| 章 | checker 符合性 | reviewer 品質 | 退回次數 | 主 agent 決策 |
|----|----------------|---------------|----------|-----------------|
| Ch.1 | PASS | PASS | 0 | 收下 |
| Ch.2 | PASS | MAJOR→PASS | 1 | 修正後收下 |

## Ch.{N} checker 符合性摘要
逐項列故事文件落差及硬性規範證據。

## Ch.{N} reviewer 品質摘要
逐項列台詞問題、聽眾效果及修正方向。

## 主 agent 決策與行動
記錄採納的問題、退回或收下的理由、下一輪修正方向，以及需人類確認的設定歧義。
```
