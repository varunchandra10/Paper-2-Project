import os
import sys
import json
import time
import datetime
import traceback
from collections import Counter

# ---- PATH SETUP ----
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

PAPERS_DIR = os.path.join(BACKEND_DIR, 'papers', 'research_papers')
REPORTS_DIR = os.path.join(BACKEND_DIR, 'tests', 'reports')
CHECKPOINT_FILE = os.path.join(REPORTS_DIR, 'checkpoint_results.json')
os.makedirs(REPORTS_DIR, exist_ok=True)

# ---- AUTO-DETECT SPECIFICATIONS ----
import requests
import subprocess

PREFERRED_MODELS = ['qwen2.5-coder:1.5b', 'qwen2.5-coder:7b', 'llama3', 'mistral', 'gemma']
MODEL_NAME = 'qwen2.5-coder:1.5b'
try:
    resp = requests.get('http://localhost:11434/api/tags', timeout=5)
    available = [m['name'] for m in resp.json().get('models', [])]
    for pref in PREFERRED_MODELS:
        if pref in available:
            MODEL_NAME = pref
            break
    if available and MODEL_NAME not in available:
        MODEL_NAME = available[0]
except Exception:
    pass

system_ram_gb = 16.0
try:
    import psutil
    system_ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
except Exception:
    pass

gpu_model = 'CPU (no GPU detected)'
vram_gb = 0.0
try:
    import torch
    if torch.cuda.is_available():
        gpu_model = torch.cuda.get_device_name(0)
        vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 1)
    else:
        raise RuntimeError("No CUDA")
except Exception:
    try:
        smi_name = subprocess.check_output(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], timeout=5, text=True).strip().splitlines()[0]
        smi_mem = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'], timeout=5, text=True).strip().splitlines()[0]
        gpu_model = smi_name
        vram_gb = round(int(smi_mem) / 1024, 1)
    except Exception:
        pass

TIMELINE_WEEKS = 2
CONSTRAINTS = {
    'gpu_model': gpu_model,
    'system_ram_gb': system_ram_gb,
    'vram_gb': vram_gb,
    'timeline_weeks': TIMELINE_WEEKS
}

# ---- LOAD CHECKPOINT IF EXISTS ----
checkpoint_data = {}
if os.path.exists(CHECKPOINT_FILE):
    try:
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
        print(f"[RESUME] Loaded {len(checkpoint_data)} previously completed paper results from checkpoint!")
    except Exception as e:
        print(f"[WARN] Failed to load checkpoint: {e}")

# ---- DISCOVER ALL PDFs ----
all_pdfs = sorted(
    [os.path.join(PAPERS_DIR, f) for f in os.listdir(PAPERS_DIR) if f.lower().endswith('.pdf')],
    key=lambda p: int(''.join(filter(str.isdigit, os.path.basename(p))) or '0')
)

from pipeline import graph as orchestrator

def save_checkpoint(pdf_name, data):
    checkpoint_data[pdf_name] = data
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

def run_corpus():
    run_start_time = time.time()
    RUN_TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("=" * 65)
    print(f"RUNNING PIPELINE FOR {len(all_pdfs)} PAPERS (WITH AUTO-SAVE & RESUME)")
    print(f"Model: {MODEL_NAME} | GPU: {gpu_model} ({vram_gb} GB VRAM)")
    print("=" * 65)

    all_results = []
    all_errors = []

    for paper_idx, pdf_path in enumerate(all_pdfs, 1):
        pdf_name = os.path.basename(pdf_path)
        paper_id = f"paper_{pdf_name.replace('[', '').replace('].pdf', '')}"

        # Check if already processed in checkpoint
        if pdf_name in checkpoint_data:
            cp = checkpoint_data[pdf_name]
            if cp.get('status') == 'SUCCESS':
                print(f"[{paper_idx:>2}/{len(all_pdfs)}] SKIPPING {pdf_name} (Already completed in checkpoint)")
                all_results.append(cp)
                continue

        print()
        print("=" * 65)
        print(f"[{paper_idx:>2}/{len(all_pdfs)}] Processing: {pdf_name}")
        print("=" * 65)

        initial_state = {
            'pdf_path': pdf_path,
            'constraints': CONSTRAINTS,
            'model_name': MODEL_NAME,
            'loop_count': 0
        }

        t0 = time.time()
        try:
            result = orchestrator.invoke(initial_state)
            elapsed = round(time.time() - t0, 2)

            gap_rpt = result.get('gap_report')
            ext_params = result.get('extracted_parameters')
            gap_counts = Counter(g.classification for g in gap_rpt.parameter_gaps) if gap_rpt else {}
            param_status_counts = dict(Counter(
                getattr(ext_params, f).status
                for f in ext_params.__class__.model_fields.keys()
            )) if ext_params else {}

            feat = result.get('feasibility_report')
            bseq = result.get('build_sequence')
            cg = result.get('component_graph')
            arpt = result.get('report')
            meta = result.get('metadata')
            pdoc = result.get('paper_doc')

            paper_result = {
                'paper_id': paper_id,
                'pdf_name': pdf_name,
                'status': 'SUCCESS',
                'elapsed_seconds': elapsed,
                'title': meta.title if meta else 'N/A',
                'authors': meta.authors if meta else [],
                'abstract': meta.abstract if meta else '',
                'primary_contribution': meta.primary_contribution if meta else '',
                'sections_count': len(pdoc.sections) if pdoc else 0,
                'tables_count': len(pdoc.tables) if pdoc else 0,
                'equations_count': len(pdoc.equations) if pdoc else 0,
                'components_count': len(cg.components) if cg else 0,
                'edges_count': len(cg.edges) if cg else 0,
                'components': [{'name': c.name, 'type': c.type, 'params': list(c.parameters.keys())} for c in cg.components] if cg else [],
                'edges': cg.edges if cg else [],
                'param_status_counts': param_status_counts,
                'gap_counts': dict(gap_counts),
                'gaps': [{'parameter': g.parameter_name, 'classification': g.classification, 'value': g.value, 'details': g.details} for g in gap_rpt.parameter_gaps] if gap_rpt else [],
                'has_critical_missing': gap_rpt.has_critical_missing_parameters if gap_rpt else None,
                'feasibility_status': feat.overall_status if feat else 'N/A',
                'feasibility_details': {
                    'overall_status': feat.overall_status if feat else 'N/A',
                    'training_status': feat.training_status if feat else 'N/A',
                    'training_substitute': feat.training_substitute if feat else '',
                    'components': [{'name': cf.component_name, 'status': cf.status, 'reason': cf.reason} for cf in getattr(feat, 'components_analysis', [])] if feat else []
                },
                'milestones_count': len(bseq.milestones) if bseq else 0,
                'total_duration_weeks': getattr(bseq, 'total_duration_weeks', 0) if bseq else 0,
                'milestones': [{'name': ms.name, 'duration_days': getattr(ms, 'estimated_duration_days', 3), 'priority': getattr(ms, 'priority', 'MEDIUM')} for ms in bseq.milestones] if bseq else [],
                'adaptation_report': {
                    'executive_summary': getattr(arpt, 'executive_summary', getattr(arpt, 'markdown_content', '')[:300]) if arpt else '',
                    'bottleneck_analysis': getattr(arpt, 'bottleneck_analysis', '') if arpt else '',
                    'cloud_migration_guide': getattr(arpt, 'cloud_migration_guide', '') if arpt else ''
                }
            }

            all_results.append(paper_result)
            save_checkpoint(pdf_name, paper_result)
            print(f"  [OK] Done in {elapsed}s (Saved to checkpoint disk file!)")

        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            err_msg = str(e)
            print(f"  [ERROR] {pdf_name} failed after {elapsed}s: {err_msg}")
            err_data = {
                'paper_id': paper_id,
                'pdf_name': pdf_name,
                'status': 'ERROR',
                'elapsed_seconds': elapsed,
                'error': err_msg,
                'traceback': traceback.format_exc()
            }
            all_errors.append(err_data)

    # ---- WRITE FINAL REPORTS ----
    report_md_path = os.path.join(REPORTS_DIR, f'corpus_report_{RUN_TS}.md')
    report_json_path = os.path.join(REPORTS_DIR, f'corpus_report_{RUN_TS}.json')

    total_run_time = round(time.time() - run_start_time, 2)
    avg_elapsed = round(sum(r['elapsed_seconds'] for r in all_results) / len(all_results), 1) if all_results else 0
    total_components = sum(r['components_count'] for r in all_results)
    total_edges = sum(r['edges_count'] for r in all_results)
    all_feasibility = Counter(r['feasibility_status'] for r in all_results)
    all_gap_counts = Counter()
    for r in all_results:
        all_gap_counts += Counter(r.get('gap_counts', {}))

    md = []
    md.append('# Paper-to-Project: Phase 1–5 Corpus-Wide Report')
    md.append(f'**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    md.append(f'**Model:** `{MODEL_NAME}`')
    md.append(f'**GPU:** {gpu_model} ({vram_gb} GB VRAM) | **RAM:** {system_ram_gb} GB')
    md.append(f'**Papers Run:** {len(all_pdfs)} | **Success:** {len(all_results)} | **Errors:** {len(all_errors)}')
    md.append('')
    md.append('## Per-Paper Results Summary')
    md.append('| # | PDF | Status | Time(s) | Comps | Edges | Feasibility | Title |')
    md.append('|---|-----|--------|---------|-------|-------|-------------|-------|')
    for i, r in enumerate(all_results, 1):
        md.append(f"| {i} | {r['pdf_name']} | OK | {r['elapsed_seconds']} | {r['components_count']} | {r['edges_count']} | {r['feasibility_status']} | {r['title'][:50].replace('|','-')} |")
    
    with open(report_md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    json_report = {
        'generated_at': datetime.datetime.now().isoformat(),
        'system': {'model': MODEL_NAME, 'gpu': gpu_model, 'vram_gb': vram_gb},
        'papers_total': len(all_pdfs),
        'papers_success': len(all_results),
        'papers_error': len(all_errors),
        'papers': all_results,
        'errors': all_errors
    }
    with open(report_json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 65)
    print("ALL REPORTS & CHECKPOINTS SUCCESSFULLY SAVED TO DISK!")
    print(f"MD Report   : {report_md_path}")
    print(f"JSON Report : {report_json_path}")
    print(f"Checkpoint  : {CHECKPOINT_FILE}")
    print("=" * 65)

if __name__ == '__main__':
    run_corpus()
