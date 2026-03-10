# Windows Build Guide

更新时间：2026-03-10

本文面向 Windows + PowerShell 环境，说明当前仓库的标准构建方式。
当前主入口已经统一为根目录的 `build.py`。

## 1. 推荐入口

```powershell
python build.py validate
python build.py rst
python build.py word
python build.py html
python build.py pdf
python build.py all
python build.py clean
```

说明：

- `rst` 只生成 RST bundle
- `word` 会先生成 RST，再导出 Word
- `html` 会先生成 RST，再导出 HTML
- `pdf` 会先生成 RST，再导出 PDF
- `all` 会一次性构建 `html + word + pdf`
- `validate` 会校验 `config.yaml` 和 `layout_params.csv`
- `clean` 会删除 `docs/_build` 和 `docs/renderers/latex/params.tex`
  这是全量清理入口

默认行为：

- 默认读取 `config.yaml`
- 默认遍历配置文件里的 `build.targets`
- 默认带 `--clean`
- 默认带 `--no-open`
- `--clean` 只清当前 target 的输出目录，并顺带清理该 target 对应的旧布局历史产物

这套命令不依赖 `make`，适合 Windows、本地 CI、GitHub Actions、macOS。

---

## 2. 前提

### 2.1 进入仓库

```powershell
cd C:\Users\Administrator\Documents\GitHub\CMS\auto-manual
```

### 2.2 激活虚拟环境

```powershell
.venv\Scripts\Activate.ps1
```

如果 PowerShell 禁止脚本执行，可先在当前终端临时放开：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
```

如果你不想激活虚拟环境，也可以直接写成：

```powershell
.\.venv\Scripts\python.exe build.py rst
```

### 2.3 系统依赖

- PDF 需要 `xelatex`
- `word_source=latex` 或 `word_source=html` 需要 `pandoc`
- `word_source=bundle` 时：
  - Windows 走 Word COM，可不依赖 `pandoc`
  - macOS / Linux 走 `pandoc`

---

## 3. 配置文件写法

批量构建的关键是 `build.targets`。

```yaml
build:
  languages: [en]
  default_region: US
  targets:
    - model: JE-2000F
      region: US
    - model: JE-1000F
      region: US
```

说明：

- `python build.py rst|word|html|pdf|all` 会遍历 `build.targets`
- 每个 target 都按 `model + region` 单独构建
- `region` 可以省略，省略时回退到 `build.default_region`

如果是 JP 配置，建议单独维护 `config.ja.yaml` 里的 `build.targets`。

---

## 4. 标准命令

### 4.1 校验配置

```powershell
python build.py validate
```

等价到底层命令：

```powershell
python tools\validate_config.py --config config.yaml
python tools\validate_layout_params.py --csv data\layout_params.csv
```

### 4.2 只生成 RST bundle

```powershell
python build.py rst
```

等价到底层命令：

```powershell
python tools\build_docs.py --config config.yaml --all-targets --prepare-only --clean --no-open
```

### 4.3 构建 Word

```powershell
python build.py word
```

等价到底层命令：

```powershell
python tools\build_docs.py --config config.yaml --all-targets --formats word --clean --no-open
```

### 4.4 构建 HTML

```powershell
python build.py html
```

等价到底层命令：

```powershell
python tools\build_docs.py --config config.yaml --all-targets --formats html --clean --no-open
```

### 4.5 构建 PDF

```powershell
python build.py pdf
```

等价到底层命令：

```powershell
python tools\build_docs.py --config config.yaml --all-targets --formats pdf --clean --no-open
```

### 4.6 一次性构建全部产物

```powershell
python build.py all
```

等价到底层命令：

```powershell
python tools\build_docs.py --config config.yaml --all-targets --formats html,word,pdf --clean --no-open
```

---

## 5. 切换配置文件

默认读取 `config.yaml`。

如果要切到 JP 配置：

```powershell
python build.py rst --config config.ja.yaml
python build.py word --config config.ja.yaml
python build.py html --config config.ja.yaml
python build.py pdf --config config.ja.yaml
python build.py all --config config.ja.yaml
```

---

## 6. 构建单个型号

如果只是临时构建某一个型号，不想走 `build.targets`，可以直接指定：

```powershell
python build.py word --config config.yaml --model JE-2000F --region US
```

说明：

- 只要传了 `--model` 或 `--region`，`build.py` 就不会再追加 `--all-targets`
- `--region` 可以省略；省略时仍然会回退到配置里的默认 region

---

## 7. 可选参数

### 7.1 保留已有产物，不清空 `docs/_build`

```powershell
python build.py html --no-clean
```

### 7.2 允许按配置自动打开产物

```powershell
python build.py pdf --open
```

### 7.3 覆盖 PDF 后端

```powershell
python build.py pdf --pdf-mode latex
python build.py pdf --pdf-mode word
```

---

## 8. 兼容层

仓库里的 `Makefile` 还保留着，但现在只是薄封装：

```powershell
make rst
make word
make html
make pdf
make all
```

它们本质上都会转发到：

```powershell
python build.py ...
```

所以：

- Windows 没装 `make` 时，直接用 `python build.py ...`
- CI 里也建议直接用 `python build.py ...`
- 根 `docs\index.rst` 会自动汇总当前 `docs\_build\` 下已存在的 bundle

macOS / Linux 通常写成：

```bash
python3 build.py all
```

---

## 9. 输出路径

RST bundle 在：

```text
docs\_build\<model>\<region>\rst\
```

构建产物在：

```text
docs\_build\<model>\<region>\
```

常见子目录：

- `rst\`
- `html\`
- `word\`
- `pdf\`
- `latex\`

---

## 10. 常见问题

- `Failed to resolve Product Name from Spec_Master.csv`
  - 检查 `Spec_Master.csv` 是否存在该 `Model + Region` 的 `Row_key=product_name`
- `make : The term 'make' is not recognized ...`
  - 直接改用 `python build.py ...`
- `xelatex not found`
  - 安装 TeX Live 或 MiKTeX，并确保 `xelatex` 在 `PATH`
- `Word reference doc not found`
  - 检查 `build.word_reference_doc` 路径是否有效
