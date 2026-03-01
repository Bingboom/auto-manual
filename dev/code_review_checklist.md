# Code Review Checklist

适用范围：

* 所有 tools/*.py
* 所有 CSV → RST 渲染逻辑
* 所有构建入口脚本
* 所有参数系统相关代码

---

## 1️⃣ 结构层（Architecture Layer）

### 1.1 模块职责是否单一？

* [ ] 是否存在一个函数做了 3 件以上的事情？
* [ ] I/O 是否与核心逻辑分离？
* [ ] 逻辑是否可以被单独调用（不依赖 CLI）？

正确结构：

```python
def parse_csv(path) -> List[Row]:
    ...

def render_rows(rows) -> str:
    ...

def write_rst(path, content):
    ...
```

---

### 1.2 是否有明确的输入输出契约？

每个脚本必须说明：

* 输入文件类型
* 必需字段
* 输出文件路径
* 输出格式

---

## 2️⃣ 数据层（CSV / Snapshot 安全）

### 2.1 字段校验是否存在？

* [ ] 是否校验字段名？
* [ ] 是否校验必填字段？
* [ ] 是否校验枚举值（如 level / type）？
* [ ] 是否校验多语言字段完整性？

建议必须有：

```python
def validate_schema(headers: List[str]) -> None:
```

---

### 2.2 构建是否确定性？

* [ ] glob() 是否排序？
* [ ] dict 遍历是否排序？
* [ ] 是否避免时间戳写入输出文件？
* [ ] 同 snapshot 是否 100% 可复现？

这关系到版本可追溯性（你流程里明确强调的目标）。

---

## 3️⃣ 错误处理层

### 3.1 是否 Fail Fast？

严重错误必须：

* 打印文件名
* 打印 CSV 行号
* 打印字段名
* 退出非 0 状态码

例如：

```python
raise ValueError(
    f"[schema error] {file} line {lineno}: missing field 'text_en'"
)
```

---

### 3.2 是否存在 Silent Fail？

* [ ] 是否有 except: pass？
* [ ] subprocess 是否检查 returncode？
* [ ] 是否存在 try/except 包住整个 main()？

严禁“执行没反应”。

---

## 4️⃣ 渲染安全层（RST / LaTeX）

### 4.1 是否统一 escape？

必须有集中函数：

```python
def escape_rst(text: str) -> str:
    ...

def escape_latex(text: str) -> str:
    ...
```

禁止在代码里散落 replace()。

---

### 4.2 raw:: latex 是否受控？

* [ ] 是否只允许白名单组件？
* [ ] 是否禁止 CSV 直接写 raw 指令？

---

## 5️⃣ 副作用控制

* [ ] 所有写入是否集中在 docs/ 或 build/？
* [ ] 是否有危险删除操作？
* [ ] 是否支持 --dry-run？

---

## 6️⃣ 日志可读性

每个阶段必须有：

```
[phase1] validating csv...
[phase2] rendering rst...
[phase3] building latex...
```

不允许黑盒执行。

---

## 7️⃣ 可测试性

* [ ] 核心逻辑是否是纯函数？
* [ ] 是否能用一个小 CSV 跑完整流程？
* [ ] 是否可写最小 regression 样例？

