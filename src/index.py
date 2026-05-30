#!/usr/bin/env python3
"""
pipeline-debugger — data pipeline logs + schema → root cause of data failures
Traces lineage, identifies transformation errors, schema drift,
volume anomalies, late arrivals — works with dbt, Airflow, Spark, Kafka
"""
import anthropic, json, re, sys
from pathlib import Path

SYSTEM = """You are a senior data engineer with deep expertise in pipeline debugging,
data quality, and distributed systems.

Analyze this pipeline failure and trace it to the root cause.

Return ONLY valid JSON — no markdown, no explanation.

{
  "failure_summary": "one sentence: what failed and why",
  "root_cause": {
    "type": "schema_drift|null_values|volume_anomaly|late_arrival|transformation_error|dependency_failure|resource_exhaustion|code_bug|configuration|network|permission|other",
    "description": "detailed root cause explanation",
    "confidence": "high|medium|low",
    "first_occurrence": "timestamp or null",
    "upstream_source": "the originating system/table/job that caused this"
  },
  "failure_chain": [
    {
      "stage": "pipeline stage or job name",
      "failure_type": "string",
      "error_message": "relevant error text",
      "downstream_impact": ["what broke because of this stage"]
    }
  ],
  "affected_datasets": [
    {
      "table_or_topic": "name",
      "impact": "data_loss|stale_data|corrupt_data|delayed|schema_changed",
      "rows_affected": number_or_null,
      "time_window": "string or null"
    }
  ],
  "schema_analysis": {
    "drift_detected": true_or_false,
    "new_columns": ["list"],
    "removed_columns": ["list"],
    "type_changes": [{"column":"string","from":"string","to":"string"}],
    "nullable_changes": [{"column":"string","was":"NOT NULL","now":"NULL"}]
  },
  "volume_analysis": {
    "anomaly_detected": true_or_false,
    "expected_rows": number_or_null,
    "actual_rows": number_or_null,
    "deviation_pct": number_or_null,
    "zero_rows": true_or_false,
    "duplicate_rows": number_or_null
  },
  "fix": {
    "immediate": "what to do right now to stop the bleeding",
    "root_fix": "permanent fix to prevent recurrence",
    "steps": ["ordered remediation steps with specific commands where possible"],
    "estimated_fix_time": "string",
    "requires_backfill": true_or_false,
    "backfill_scope": "string or null"
  },
  "prevention": [
    {
      "measure": "preventive measure",
      "implementation": "how to implement it (dbt test, Airflow sensor, Great Expectations, etc.)",
      "detects": "what class of issues this would catch"
    }
  ],
  "monitoring_recommendations": [
    {
      "metric": "what to monitor",
      "threshold": "alert threshold",
      "tool": "Grafana|CloudWatch|dbt|Great Expectations|Airflow|custom"
    }
  ],
  "code_fix_hint": "relevant code snippet or config change if applicable",
  "related_issues": ["similar issues to check or fix proactively"],
  "confidence": 0.0
}"""

def debug(log_text: str, schema_text: str = "", pipeline_type: str = "auto") -> dict:
    client = anthropic.Anthropic()
    context_parts = [
        f"Pipeline type: {pipeline_type}" if pipeline_type != "auto" else "",
        f"Error logs:\n{log_text[:20000]}",
        f"\nSchema/config:\n{schema_text[:10000]}" if schema_text else ""
    ]
    prompt = "\n".join(p for p in context_parts if p)
    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=3000, system=SYSTEM,
        messages=[{"role":"user","content":f"Debug this pipeline failure:\n\n{prompt}"}]
    )
    raw = re.sub(r'^```(?:json)?\s*','',resp.content[0].text.strip(),flags=re.MULTILINE)
    raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE)
    return json.loads(raw)

def print_report(r: dict):
    rc = r.get("root_cause",{})
    fix = r.get("fix",{})
    vol = r.get("volume_analysis",{})
    schema = r.get("schema_analysis",{})
    conf_bar = {"high":"●●●","medium":"●●○","low":"●○○"}.get(rc.get("confidence","low"),"○○○")

    print(f"\n{'═'*60}")
    print(f"  PIPELINE DEBUGGER")
    print(f"  Root cause: {rc.get('type','?').upper().replace('_',' ')}")
    print(f"  Confidence: {conf_bar}")
    print(f"{'═'*60}")
    print(f"\n  {r.get('failure_summary','')}")
    print(f"\n  Root cause:\n  {rc.get('description','')}")
    if rc.get("upstream_source"): print(f"  Origin: {rc['upstream_source']}")

    chain = r.get("failure_chain",[])
    if chain:
        print(f"\n  FAILURE CHAIN")
        for stage in chain:
            print(f"  → {stage.get('stage','?')}: {stage.get('failure_type','')}")
            if stage.get("error_message"): print(f"     \"{stage['error_message'][:80]}\"")

    if vol.get("anomaly_detected"):
        print(f"\n  VOLUME ANOMALY")
        print(f"  Expected: {vol.get('expected_rows','?'):,} | Actual: {vol.get('actual_rows','?'):,} | Deviation: {vol.get('deviation_pct','?')}%")
        if vol.get("zero_rows"): print(f"  ⚠ ZERO ROWS — table is empty")

    if schema.get("drift_detected"):
        print(f"\n  SCHEMA DRIFT DETECTED")
        if schema.get("new_columns"): print(f"  New: {', '.join(schema['new_columns'])}")
        if schema.get("removed_columns"): print(f"  Removed: {', '.join(schema['removed_columns'])}")
        for tc in schema.get("type_changes",[]): print(f"  Type change: {tc.get('column','')} {tc.get('from','')} → {tc.get('to','')}")

    print(f"\n  FIX")
    print(f"  ⚡ Now: {fix.get('immediate','')}")
    print(f"  🔧 Root fix: {fix.get('root_fix','')}")
    for step in fix.get("steps",[])[:4]: print(f"  → {step}")
    if fix.get("requires_backfill"): print(f"  ⚠ Backfill required: {fix.get('backfill_scope','?')}")
    if r.get("code_fix_hint"): print(f"\n  Code hint:\n  {r['code_fix_hint'][:150]}")

    prev = r.get("prevention",[])
    if prev:
        print(f"\n  PREVENTION")
        for p in prev[:3]: print(f"  🛡 {p.get('measure','')} [{p.get('tool','')}]")

    print(f"\n  Confidence: {int(r.get('confidence',0)*100)}%")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Debug data pipeline failures")
    p.add_argument("logs", help="Error log file or '-' for stdin")
    p.add_argument("--schema","-s",default="",help="Schema or config file for context")
    p.add_argument("--type","-t",default="auto",help="Pipeline type: dbt|airflow|spark|kafka|flink")
    p.add_argument("--json",action="store_true")
    a = p.parse_args()
    logs = sys.stdin.read() if a.logs=="-" else (Path(a.logs).read_text(encoding="utf-8",errors="replace") if Path(a.logs).exists() else a.logs)
    schema = Path(a.schema).read_text(encoding="utf-8",errors="replace") if a.schema and Path(a.schema).exists() else a.schema
    r = debug(logs, schema, a.type)
    if a.json: print(json.dumps(r,indent=2,ensure_ascii=False))
    else: print_report(r)
