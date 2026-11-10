---
name: eloicontent_creating
description: ASMR 音聲劇本（草稿流程）初稿撰寫。當使用者要求撰寫商業作品初稿、進入草稿階段、或 workflow 指示執行此 skill 時觸發。
---


## Input

- 故事文件路徑（`workspace/{角色名}/故事文件/{作品名}.md`）
- 寫作指引 (`specs/writing/劇本寫作指引.md`)
- 迭代次數（loop_total，1～5）

工作區資料夾已由 workflow 建好（`workspace/{角色名}/{model}_loop{N}_草稿/`）。

> B 階段依故事文件寫稿。
> **模型由 `assign-writing-task` skill 預設**

---

## 執行流程

### 準備階段

確認章節數：讀取故事文件，找出大綱的章節總數（共幾章）。

---

### Loop 迭代（重複 loop_total 次）

```
for loop_n in 1 .. loop_total:
```

**work_dir** = `workspace/{角色名}/{model}_loop{loop_n}_草稿/`

---

#### 1. 合併上一 loop 草稿（loop_n > 1 時）

執行：
```bash
python .agents/skills/eloicontent_creating/scripts/merge_draft_chapters.py \
  --dir workspace/{角色名}/{model}_loop{loop_n-1}_草稿 \
  --chapters 1-{章節總數}
```

輸出路徑：`{model}_loop{loop_n-1}_草稿/{model}_loop{loop_n-1}_草稿.md`

將此合併檔作為 **prev_draft** 傳入本 loop。

---

#### 2. 逐章寫稿與審查

讀取並執行 `.agents/skills/assign-writing-task.md`，逐章走完「writer → checker → reviewer → 主 agent 決策」流程。

**每章派發 writer subagent 時注入：**

| 項目 | 內容 |
|---|---|
| 寫作指引 | `specs/writing/劇本寫作指引.md`（完整內容） |
| 任務說明 | `workflow/B階段任務說明.md`（完整內容） |
| 故事文件 | （完整內容） |
| 上一 loop 修改說明 | loop_n > 1 時（`{model}_loop{loop_n-1}_草稿/loop{loop_n}_修改說明.md`，完整內容） |
| prev_draft | loop_n > 1 時（上一 loop 合併草稿，完整內容） |
| 人類調整建議 | 上一 loop handoff 內人類寫的建議（若有） |


**每章派發 checker subagent 時注入：**
- 故事文件、本章稿件、已接受的前章與人類明示的例外
- `specs/standards/草稿總審查標準.md` 的故事文件對照項目
- `specs/standards/草稿撰寫審查標準.md` 的硬性格式項目及寫作指引

**每章派發 reviewer subagent 時注入：**
- 審查標準：`specs/standards/草稿撰寫審查標準.md`（完整內容）——reviewer 所屬的文字、台詞、節奏與連貫性項目
- writer 產出的該章稿件
- 人類於上一 loop handoff 寫的調整建議（若有，reviewer 依人類明示偏好調整相應項目）

**退回與章節推進：**
- checker 與 reviewer 各交獨立報告；主 agent 綜合判斷是否退回重寫
- writer 修稿後由主 agent 重派受影響的 checker／reviewer 複審，人類不參與
- 章節通過後推進下一章，直到本 loop 全部章節完成

> 審查標準、退回機制、report 格式由 `assign-writing-task` 與 `specs/standards/草稿撰寫審查標準.md` 定義，本檔不重複。

---

#### 3. Loop 完成——主 agent 報告與人類建議

本 loop 所有章節完成後，主 agent 收到 checker 與 reviewer 的報告並彙整 report.md，再向使用者報告：

```
Loop {loop_n}/{loop_total} 完成

各章審查結果：
- Ch.1：{PASS / MINOR / MAJOR}
- Ch.2：{PASS / MINOR / MAJOR}
- ...

請確認是否繼續 Loop {loop_n+1}？
若要調整下一 loop 的審查方向，請在 handoff.md 寫建議。
```

主 agent 產出 `{work_dir}/handoff.md`（走 `handoff` skill §一.1），人類閱讀後可在 handoff 內寫調整建議，影響下一 loop 的 writer 注入、checker 的明示例外與 reviewer 的品質偏好。

---

#### 4. 交接

讀取並執行 `.agents/skills/handoff.md`：

- **§一.1**：產出 `{work_dir}/handoff.md`（固定執行，含審查摘要與心得）
- **§二.1**：產出 `{work_dir}/loop{loop_n+1}_修改說明.md`（loop_n < loop_total 且使用者確認繼續時；最後一個 loop 也預設生成）

---

### 結束條件

以下任一成立時結束：
- 完成 loop_total 次迭代
- 使用者在 loop 完成確認時選擇不繼續

---

## Output

| 檔案 | 說明 |
|------|------|
| `{model}_loop{N}_草稿/ch{M}.md` | 各 loop 各章節草稿 |
| `{model}_loop{N}_草稿/loop{N+1}_修改說明.md` | 下一 loop 的改進方向（最後一個 loop 不生成） |
| `{model}_loop{N}_草稿/{model}_loop{N}_草稿.md` | 合併草稿（loop_n > 1 時生成，供下一 loop 參考） |
| `{model}_loop{N}_草稿/handoff.md` | 交接文件（每個 loop 結束後固定產出） |
| `{model}_loop{N}_草稿/report.md` | 主 agent 彙整 checker 與 reviewer 獨立結果及決策 |

---

## 接手交接

當新 session 收到以下格式的啟動指令時：

> 請繼續 B 階段 Loop {N+1}，交接文件路徑：`{handoff_path}`

讀取並執行 `.agents/skills/handoff.md` **§一.2 接手新 session**。

