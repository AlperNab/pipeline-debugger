# Pipeline Debugger — Standalone Real GUI Implementation

This folder is now its own runnable project app. It does not depend on the root all-project dashboard at runtime.

## Run

```bash
./run_gui.sh
```

Windows:

```powershell
.\run_gui_windows.ps1
```

Default URL: `http://127.0.0.1:9146`

## What is inside this project folder

- `app/` — FastAPI backend for this project.
- `static/` — elegant browser GUI.
- `plugins/pipeline-debugger.json` — this project’s own feature/customization/input schema.
- `project_config.json` — readable copy of the same project-specific configuration.
- `data/` — local SQLite jobs, uploads, exports.
- `tests/` — verifies this project has a registered real local engine.

## Project-specific scope

- Domain: `DevOps / CI/CD`
- Target user: `Domain operator, business owner, analyst, or team member who needs this workflow executed reliably.`
- Core job: Pipeline logs/config → failure diagnosis
- Suite: `Developer Productivity Suite`

## Deep features applied

- failing step detection
- config diff
- dependency/cache issue classifier
- retry safety
- patch recommendation
- CI provider integration
- incident link

## Customization controls

- `execution_mode` — Execution mode (select)
- `ci_provider` — CI provider (text)
- `repo` — repo (text)
- `branch` — branch (text)
- `environment` — environment (text)
- `severity` — severity (text)
- `retry_rules` — retry rules (textarea)
- `secret_redaction` — secret redaction (text)
- `output_format` — output format (select)
- `language` — language (select)
- `privacy_mode` — privacy mode (select)
- `confidence_threshold` — Confidence threshold (slider)

## Input fields

- `pipeline_logs` — Pipeline logs (text) required
- `config` — config (text) required
- `work_brief` — Work brief / source text / URL / instructions (textarea) required

## External data policy

The local deterministic core is real and executable. Live external systems are not simulated. If Shopify, ATS, ERP, OCR/STT, maps, SERP, market data, medical databases, tax/customs databases, or other live systems are required, this project reports the missing connector/API requirement instead of inventing data.

---

## Final UX/UI Layer

This project now uses the **Developer Workbench** pattern.

**UX workflow:** Code/schema/log intake → analysis → diff/tests/docs → implementation checklist

**Domain components:**
- Code/source panel
- File tree summary
- Diff and patch viewer
- Test/result board
- API/schema preview

**Quick actions:**
- Analyze source
- Generate patch/checklist
- Create tests
- Build docs/schema output

**No fake-data policy:** external/live actions require real connectors or API keys. Missing connectors are reported instead of simulated.
