# PR 标题

[Feature/Fix/Refactor] 简短说明

---

## 变更类型

* [ ] 新功能
* [ ] Bug 修复
* [ ] 架构优化
* [ ] 性能优化
* [ ] 参数系统修改
* [ ] 构建流程修改

---

## 影响范围

* [ ] CSV Schema
* [ ] 渲染逻辑
* [ ] 参数系统
* [ ] 构建入口
* [ ] LaTeX 组件
* [ ] 无破坏性影响

---

## Code Review Checklist

### 数据安全

* [ ] 字段校验存在
* [ ] 枚举校验存在
* [ ] 多语言字段校验

### 构建确定性

* [ ] 所有 glob 已排序
* [ ] 无时间戳污染
* [ ] 同输入可复现

### 错误处理

* [ ] 无 silent fail
* [ ] subprocess returncode 检查
* [ ] 报错可定位 CSV 行

### 渲染安全

* [ ] 统一 escape
* [ ] raw 指令受控

---

## 回归验证

* [ ] Safety 示例可正常构建
* [ ] HTML 构建正常
* [ ] PDF 构建正常
* [ ] diff 无异常噪声


