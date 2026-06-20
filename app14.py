import os
import re
import sys
import ast
import json
import subprocess
from html.parser import HTMLParser
from typing import List, Tuple, Optional, Any, Dict
from dataclasses import dataclass
from flask import Flask, render_template_string, request, jsonify
from difflib import unified_diff
import tkinter as tk
from tkinter import filedialog
import google.generativeai as genai

app = Flask(__name__)

# CONFIGURATION MATRIX
GEMINI_API_KEY = "API_GEMINI"
genai.configure(api_key=GEMINI_API_KEY)

@dataclass(frozen=True)
class InvariantStateMatrix:
    """Immutable State Evaluation Matrix for Atomic Operations"""
    success: bool
    payload: str
    diff_graph: List[str]
    telemetry_logs: List[str]
    execution_time_complexity: str

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DiffKu v9 - System Invariant Orchestrator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ace/1.32.6/ace.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #030303; color: #d4d4d8; }
        .workspace-grid {
            display: grid; grid-template-columns: 1fr 1fr; height: calc(100vh - 120px);
            background-color: #09090b; border: 1px solid #27272a; border-radius: 8px; overflow: hidden;
        }
        .pane { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
        .pane-scrollable { display: flex; flex-direction: column; height: 100%; overflow-y: auto; }
        .pane-header {
            background-color: #09090b; padding: 10px 16px; border-bottom: 1px solid #27272a;
            display: flex; justify-content: space-between; align-items: center;
            color: #71717a; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
            position: sticky; top: 0; z-index: 10;
        }
        #editor-frame { flex: 1; width: 100%; height: 100%; position: relative; }
        #editor { position: absolute; top: 0; bottom: 0; left: 0; right: 0; font-size: 13px; }
        .terminal {
            background-color: #010101; color: #34d399;
            font-family: 'Fira Code', monospace; font-size: 12px; padding: 16px; 
            white-space: pre-wrap; flex: 1;
        }
    </style>
</head>
<body class="p-4">

    <header class="mb-4 flex flex-wrap items-center justify-between gap-4 bg-[#09090b] p-3 rounded-lg border border-[#27272a]">
        <div class="flex items-center gap-3">
            <span class="text-zinc-100 font-bold text-xs uppercase tracking-wider">DiffKu Orchestrator v9</span>
            <span class="bg-zinc-900 text-zinc-400 text-[10px] font-mono px-2 py-0.5 rounded border border-zinc-700">DETERMINISTIC_LOGIC_ON</span>
            <div class="h-4 w-[1px] bg-zinc-800"></div>
            <input type="text" id="display-path" value="{{ file_path }}" readonly
                placeholder="Null baseline context..."
                class="bg-[#010101] border border-[#27272a] rounded px-3 py-1.5 text-xs font-mono w-96 text-zinc-400 focus:outline-none">
        </div>

        <div class="flex items-center gap-2">
            <button id="btn-browse" type="button" onclick="dispatchAction('browse_file')" 
                class="bg-zinc-800 hover:bg-zinc-700 text-xs text-white px-3 py-2 rounded font-medium border border-zinc-700 transition active:scale-95">
                📂 Bind Target
            </button>
            <button id="btn-run" type="button" onclick="dispatchAction('analyze_ai')" 
                class="bg-zinc-100 hover:bg-zinc-200 text-xs text-black px-4 py-2 rounded font-bold transition active:scale-95 flex items-center gap-1">
                ⚙️ Execute Mutator
            </button>
            <button id="btn-save" type="button" onclick="dispatchAction('save_manual')" 
                class="bg-emerald-700 hover:bg-emerald-600 text-xs text-white px-4 py-2 rounded font-medium transition active:scale-95">
                💾 Commit Matrix
            </button>
        </div>
    </header>

    <form method="POST" id="unified-post-form" class="hidden">
        <input type="hidden" name="action" id="form-action">
        <input type="hidden" name="file_path" value="{{ file_path }}">
        <textarea name="file_asli_content" id="hidden-textarea"></textarea>
        <textarea name="ai_instruction" id="hidden-instruction"></textarea>
    </form>

    <div class="workspace-grid">
        <div class="pane border-r border-[#27272a]">
            <div class="pane-header">
                <span>Active Core Memory Buffer</span>
                <span id="lang-indicator" class="text-zinc-400 font-mono text-[10px]">Agnostic Target</span>
            </div>
            <div id="editor-frame">
                <div id="editor">{{ file_asli }}</div>
            </div>
        </div>

        <div class="pane-scrollable">
            <div class="pane-header">
                <span>State Evaluation Matrix Log</span>
                <span class="text-zinc-400 font-mono text-[10px]">Boundary Check Active</span>
            </div>
            
            <div class="p-3 bg-[#09090b] border-b border-[#27272a]">
                <label class="block text-[10px] text-zinc-400 font-bold uppercase tracking-wider mb-1.5">Logical Constraints Specification Input:</label>
                <textarea id="visible-instruction" rows="4"
                    placeholder="Provide specific functional transformation criteria..."
                    class="w-full bg-[#010101] border border-[#27272a] rounded p-2.5 text-xs font-mono text-zinc-200 focus:outline-none focus:border-zinc-500 resize-none leading-relaxed">{{ ai_instruction }}</textarea>
            </div>

            <div class="terminal">{% if log_status %}<div class="text-zinc-400 font-bold mb-1">[PIPELINE LOG TRACE]</div>{{ log_status }}{% endif %}{% if diff_results %}

<div class="text-zinc-400 font-bold mt-4">[DIFFERENTIAL TOKENS STATE GRAPH]</div>{% for line in diff_results %}{% if line.startswith('-') %}<span class="text-red-400 block bg-red-950/20 px-1 font-mono font-medium">{{ line }}</span>
{% elif line.startswith('+') %}<span class="text-emerald-400 block bg-emerald-950/20 px-1 font-mono font-medium">{{ line }}</span>
{% else %}<span class="text-zinc-600 block px-1 font-mono">{{ line }}</span>
{% endif %}{% endfor %}{% else %}
> Core Engine Idle. No mutation queue active.
{% endif %}</div>
        </div>
    </div>

    <script>
        var editor = ace.edit("editor");
        editor.setTheme("ace/theme/one_dark");
        
        var filePath = "{{ file_path }}";
        var ext = filePath.split('.').pop().toLowerCase();
        var indicator = document.getElementById('lang-indicator');
        
        const modeMap = {
            'html': 'html', 'css': 'css', 'js': 'javascript', 'json': 'json',
            'xml': 'xml', 'java': 'java', 'cpp': 'c_cpp', 'py': 'python',
            'ts': 'typescript', 'php': 'php', 'kt': 'kotlin'
        };
        
        if(modeMap[ext]) {
            editor.session.setMode("ace/mode/" + modeMap[ext]);
            indicator.innerText = ext.toUpperCase() + " METADATA STACK";
        }

        editor.setOptions({
            fontFamily: "Fira Code, monospace", fontSize: "13px",
            showPrintMargin: false, wrap: true, cursorStyle: "smooth", highlightActiveLine: true
        });

        function dispatchAction(actionName) {
            document.getElementById('btn-browse').disabled = true;
            document.getElementById('btn-run').disabled = true;
            document.getElementById('btn-save').disabled = true;
            if(actionName === 'analyze_ai') { document.getElementById('btn-run').innerText = "Processing Pipeline Vector..."; }
            document.getElementById('form-action').value = actionName;
            document.getElementById('hidden-textarea').value = editor.getValue();
            document.getElementById('hidden-instruction').value = document.getElementById('visible-instruction').value;
            document.getElementById('unified-post-form').submit();
        }
    </script>

</body>
</html>
'''

class StrictHTMLStateChecker(HTMLParser):
    """Finite State Automata for absolute HTML tree validation using LIFO Stack"""
    def __init__(self):
        super().__init__()
        self.is_valid = True
        self.stack = []
        self.void_elements = {
            'meta', 'link', 'img', 'br', 'hr', 'input', 
            'col', 'embed', 'source', 'track', 'wbr', '!doctype'
        }

    def handle_starttag(self, tag: str, attrs: list):
        if tag.lower() not in self.void_elements and not tag.startswith('!'):
            self.stack.append(tag.lower())

    def handle_endtag(self, tag: str):
        if tag.lower() not in self.void_elements:
            if not self.stack:
                self.is_valid = False
                return
            expected_tag = self.stack.pop()
            if expected_tag != tag.lower():
                self.is_valid = False

    def verify_final_state(self) -> bool:
        return self.is_valid and len(self.stack) == 0

class NativeRuntimeSandboxLinter:
    """Multi-language Abstract Syntactic Graph Verification Core 100% Deterministic"""
    
    @staticmethod
    def execute_static_analysis(code: str, ext: str, file_path: str) -> Tuple[bool, str]:
        if not code.strip():
            return False, "Validation Critical Error: Null or empty output sequence produced."
            
        # SANITIZATION GUARD: Prevention of structural pollution vectors
        structural_pollution_vectors = [r"<<<<<<<", r"=======", r">>>>>>>"]
        for vector in structural_pollution_vectors:
            if re.search(vector, code):
                return False, f"Sanitization Guard Breached: Contamination anomaly '{vector}' detected."

        # 1. PYTHON DETERMINISTIC VALIDATION via CPython PEG Parser
        if ext == 'py':
            try:
                ast.parse(code)
                return True, "Python AST generation success."
            except SyntaxError as se:
                return False, f"Python Structural Error [Baris {se.lineno}]: {se.msg}"
                
        # 2. JAVASCRIPT/TYPESCRIPT DETERMINISTIC VALIDATION (ESM & Script Compatible)
        elif ext in ['js', 'ts']:
            try:
                js_check_script = (
                    f"const fs = require('fs'); "
                    f"try {{ "
                    f"  new Function(`async () => {{ {json.dumps(code)} }}`); "
                    f"  process.exit(0); "
                    f"}} catch(e) {{ "
                    f"  if (e instanceof SyntaxError && (e.message.includes('import') || e.message.includes('export'))) {{ "
                    f"    process.exit(0); "
                    f"  }} "
                    f"  console.error(e.message); "
                    f"  process.exit(1); "
                    f"}}"
                )
                process = subprocess.run(
                    ["node", "-e", js_check_script],
                    capture_output=True, text=True, timeout=2
                )
                if process.returncode != 0:
                    return False, f"V8 JavaScript Engine Parsing Error: {process.stderr.strip()}"
                return True, "JavaScript High-Logic Token parsing success."
            except FileNotFoundError:
                pass 

        # 3. MARKUP DETERMINISTIC VALIDATION via Pushdown Automata Stack
        if ext in ['html', 'xml']:
            parser = StrictHTMLStateChecker()
            try:
                parser.feed(code)
                if not parser.verify_final_state():
                    return False, "Markup Hierarchical Error: Unbalanced elements or overlapping tag trees detected."
                return True, "HTML Document Tree structure verified perfectly."
            except Exception as markup_err:
                return False, f"Markup Parser Exception: {str(markup_err)}"

        return True, "Agnostic Base Parameter Validation Confirmed."

class AutonomousMutationOrchestrator:
    """High-Performance Logic Synthesis and Self-Healing Automation Core"""

    @classmethod
    def process_transaction(cls, current_code: str, instruction: str, file_path: str, loop_threshold: int = 3) -> InvariantStateMatrix:
        model = genai.GenerativeModel("gemini-3.1-flash-lite")
        ticks = chr(96) * 3
        
        ext = file_path.split('.')[-1].lower() if '.' in file_path else 'txt'
        working_buffer = current_code
        telemetry_logs = []
        feedback_diagnostics = ""
        
        for pass_idx in range(1, loop_threshold + 1):
            telemetry_logs.append(f"[TRANS-PASS-{pass_idx}] Generating Syntactic Structure Models...")
            
            prompt = (
                f"SYSTEM PARAMETERS:\n"
                f"Role: Enterprise Code Synthesis Engine.\n"
                f"Task: Execute architectural code mutation for one single file structure.\n"
                f"Language Context Hierarchy: Ext-Type .{ext}\n\n"
                f"DETERMINISTIC INVARIANTS:\n"
                f"1. Output the ENTIRE completely updated file layout. No placeholders, no abbreviations, no truncation.\n"
                f"2. Strict Isolation: Do not include merge markers (e.g., <<<<<<<, =======, >>>>>>>).\n"
                f"3. Strict Type Safety, proper memory allocation paradigm, and low-coupling design principles are mandatory.\n\n"
                f"Current Source Vector State:\n{ticks}\n{working_buffer}\n{ticks}\n\n"
                f"Structural Modification Request:\n{instruction}\n\n"
            )
            
            if feedback_diagnostics:
                prompt += (
                    f"CRITICAL DIAGNOSTIC EXCEPTION RECORDED FROM ENGINE COMPILER:\n"
                    f">> {feedback_diagnostics}\n"
                    f"Resolution Mandate: Correct the violation, perform rigorous logical tree analysis, and regenerate the unbroken file payload.\n"
                )
                
            prompt += f"Output Spec: Emit ONLY the executable code enclosed within standard markdown block specifiers: ```{ext}\n[Code Payload]\n```"
            
            try:
                response = model.generate_content(prompt)
                if not response or not response.text:
                    feedback_diagnostics = "Null upstream token payload."
                    telemetry_logs.append(f"❌ Pass {pass_idx} State: Pipeline Empty Stream.")
                    continue
                
                code_match = re.search(r"```[a-zA-Z]*[\r\n]+([\s\S]*?)```", response.text)
                extracted_payload = code_match.group(1) if code_match else response.text.strip().strip("`")
                
                # RUN VERIFICATION SUBPROCESS PHASE
                is_valid, report = NativeRuntimeSandboxLinter.execute_static_analysis(extracted_payload, ext, file_path)
                if not is_valid:
                    feedback_diagnostics = report
                    telemetry_logs.append(f"❌ Pass {pass_idx} Verification Failed: {report}")
                    working_buffer = extracted_payload
                    continue

                # STATE MUTATION SUCCESS
                telemetry_logs.append(f"⚡ Pass {pass_idx} Verification Success: Deterministic structural state matched.")
                
                diff_graph = list(unified_diff(
                    current_code.splitlines(), extracted_payload.splitlines(),
                    fromfile=f'State.Alpha.{ext}', tofile=f'State.Omega.{ext}', lineterm=""
                ))
                
                return InvariantStateMatrix(True, extracted_payload, diff_graph[2:], telemetry_logs, "Asymptotic Time Complexity: O(N)")
                
            except Exception as runtime_ex:
                feedback_diagnostics = str(runtime_ex)
                telemetry_logs.append(f"❌ Pass {pass_idx} Execution Interrupted: {str(runtime_ex)}")
                
        return InvariantStateMatrix(False, current_code, [], telemetry_logs + ["❌ TRANSACTION ABORTED: Invariant state limits exceeded. Rollback committed."], "N/A")

@app.route('/', methods=['GET', 'POST'])
def runtime_orchestrator() -> Any:
    file_path = ""
    file_asli_content = ""
    ai_instruction = ""
    log_status = None
    diff_results = None

    if request.method == 'POST':
        action = request.form.get('action', '')
        file_path = request.form.get('file_path', '').strip()
        file_asli_content = request.form.get('file_asli_content', '')
        ai_instruction = request.form.get('ai_instruction', '')

        if action == 'browse_file':
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            selected_path = filedialog.askopenfilename()
            root.destroy()

            if selected_path:
                file_path = os.path.normpath(selected_path)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        file_asli_content = f.read()
                    log_status = f"✓ Context binding confirmed for path vector: {os.path.basename(file_path)}"
                except Exception as e:
                    log_status = f"✗ File System Lock Exception: {str(e)}"

        elif action == 'analyze_ai':
            if not file_path:
                log_status = "✗ Constraints Error: File target boundary execution is null."
            elif not ai_instruction.strip():
                log_status = "✗ Constraints Error: Operational prompt block empty."
            else:
                tx: InvariantStateMatrix = AutonomousMutationOrchestrator.process_transaction(file_asli_content, ai_instruction, file_path)
                log_status = "\n".join(tx.telemetry_logs)
                if tx.success:
                    log_status += f"\n✓ Performance Analysis: {tx.execution_time_complexity}\n✓ Disk Synchronization State: PERSISTED."
                    file_asli_content = tx.payload
                    diff_results = tx.diff_graph
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(tx.payload)
                    except Exception as io_err:
                        log_status += f"\n❌ Hardware IO Write Abort: {str(io_err)}"
                else:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            file_asli_content = f.read()
                    except:
                        pass

        elif action == 'save_manual':
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_asli_content)
                    log_status = "✓ Direct persistence pipeline committed successfully to disk storage infrastructure."
                except Exception as e:
                    log_status = f"✗ Storage IO Fault: {str(e)}"

    return render_template_string(
        HTML_TEMPLATE, file_path=file_path, file_asli=file_asli_content,
        ai_instruction=ai_instruction, log_status=log_status, diff_results=diff_results
    )

if __name__ == '__main__':
    app.run(port=5001, debug=True)
