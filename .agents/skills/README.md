# Kimi Skills（项目级）

本项目级的 `.agents/skills/` 目录用于存放随项目同步的 Kimi Code CLI skills。

## 包含的 Skill

### `ipo-scoring` — IPO 标的质量评分

用于评估港股IPO招股书的标的质量，输出标准化的评分报告（Word文档）。

**触发场景：**
- 提供招股书PDF，要求评估IPO质量
- 询问是否开放孖展额度
- 按IPO Score Guidelines打分

**文件结构：**
```
ipo-scoring/
├── SKILL.md                    # 核心工作流与触发条件
├── references/
│   ├── scoring-rubric.md       # 7维度评分标准
│   └── report-spec.md          # 报告格式规范（简体+繁体）
└── scripts/
    └── generate_report.py      # Word报告生成辅助脚本
```

## 跨设备同步说明

本目录已纳入Git版本控制，随项目一起提交到GitHub后：

1. **在家电脑**：直接在此项目下使用
2. **公司电脑**：`git clone` 项目仓库，Kimi Code CLI 会自动识别 `.agents/skills/` 下的 skill，无需额外安装

## 安装验证

在公司电脑clone项目后，可以在Kimi对话中测试触发：

> "评估这份招股书"

如果skill正常加载，Kimi会按IPO评分流程开始执行。
