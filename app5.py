import os
import re
from flask import Flask, render_template_string, request
from difflib import SequenceMatcher, unified_diff

# Menggunakan tkinter untuk memanggil file picker bawaan Windows
import tkinter as tk
from tkinter import filedialog

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DiffKu Engine v3 - Real Disk Workspace</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        textarea {
            text-align: left;
            white-space: pre;
            overflow-wrap: normal;
            overflow-x: auto;
        }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">

    <header class="border-b border-slate-800 bg-slate-900/40 backdrop-blur sticky top-0 z-50 px-6 py-4 flex justify-between items-center">
        <div class="flex items-center space-x-3">
            <div class="bg-gradient-to-tr from-indigo-600 to-cyan-500 p-2 rounded-xl text-white font-bold mono text-xl tracking-wider shadow-lg">
                DK
            </div>
            <div>
                <h1 class="text-xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">DiffKu Engine v3</h1>
                <p class="text-xs text-slate-400">Real Workspace: Native File Picker & Direct Auto-Write</p>
            </div>
        </div>
        <div class="flex items-center space-x-2 text-xs bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-full">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span class="text-slate-300">Mode: Native File Explorer Access</span>
        </div>
    </header>

    <main class="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">

        <form method="POST" class="space-y-6">
            
            <!-- PANEL SELEKSI FILE OTOMATIS -->
            <div class="bg-slate-900 border border-slate-800 p-4 rounded-2xl space-y-3 shadow-xl">
                <div class="flex justify-between items-center">
                    <label class="text-xs font-bold tracking-wider text-slate-400 block">FILE TARGET YANG AKAN DIUBAH OTOMATIS</label>
                    {% if file_path %}
                    <span class="text-xs text-cyan-400 font-mono bg-cyan-950/50 px-2 py-0.5 rounded border border-cyan-900">Terhubung Riil</span>
                    {% endif %}
                </div>
                
                <div class="flex flex-col sm:flex-row gap-3">
                    <!-- Tombol ini memicu jendela pop-up File Explorer Windows -->
                    <button type="submit" name="action" value="browse_file" 
                        class="bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition active:scale-95 whitespace-nowrap shadow-md flex items-center space-x-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path></svg>
                        <span>Pilih File dari Komputer</span>
                    </button>
                    
                    <!-- Input text dikunci (readonly) hanya untuk menampilkan path yang dipilih secara otomatis -->
                    <input type="text" name="file_path" value="{{ file_path }}" readonly placeholder="Belum ada file yang dipilih... Klik tombol di samping ↗" 
                        class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm mono {% if file_path %} text-emerald-400 {% else %} text-slate-500 {% endif %} focus:outline-none tracking-normal cursor-not-allowed">
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

                <!-- PANEL KIRI: ISI FILE -->
                <div class="lg:col-span-5 flex flex-col space-y-2">
                    <div class="flex justify-between items-center">
                        <label class="text-sm font-semibold tracking-wider text-slate-400 flex items-center space-x-2">
                            <svg class="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                            <span>ISI FILE SEKARANG (LIVE EDIT)</span>
                        </label>
                        <span class="text-xs text-indigo-400 font-mono bg-indigo-950/50 px-2 py-0.5 rounded border border-indigo-900">Bisa Diedit Manual</span>
                    </div>

                    <textarea
                        name="file_asli_content"
                        rows="18"
                        class="w-full bg-slate-900 border border-slate-800 rounded-2xl p-4 mono text-xs text-emerald-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition shadow-2xl block tracking-normal leading-relaxed"
                        spellcheck="false"
                        placeholder="Isi file otomatis terisi setelah pilih file di atas...">{{ file_asli }}</textarea>
                </div>

                <!-- PANEL KANAN: AI INSTRUCTION -->
                <div class="lg:col-span-7 flex flex-col space-y-2">
                    <div class="flex justify-between items-center">
                        <label class="text-sm font-semibold tracking-wider text-slate-400 flex items-center space-x-2">
                            <svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 11-3-3V3m3 4c0 2.21-1.79 4-4 4s-4-1.79-4-4"></path></svg>
                            <span>INPUT BLOK SEARCH / REPLACE DARI AI</span>
                        </label>
                        <span class="text-xs text-amber-400 font-mono bg-amber-950/50 px-2 py-0.5 rounded border border-amber-900">Partial Patch System</span>
                    </div>
                    <textarea
                        name="ai_instruction"
                        rows="18"
                        class="w-full bg-slate-900 border border-slate-800 rounded-2xl p-4 mono text-sm text-indigo-300 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition shadow-2xl block tracking-normal leading-relaxed"
                        spellcheck="false"
                        placeholder="Ketik atau tempel potongan instruksi AI di sini...">{{ ai_instruction }}</textarea>
                </div>
            </div>

            <div class="flex flex-col sm:flex-row justify-between items-center bg-slate-900/60 p-4 rounded-2xl border border-slate-800 gap-4">
                <div class="text-xs text-slate-400 max-w-xl text-center sm:text-left leading-relaxed">
                    💾 <strong>Operasi File Otomatis:</strong> Menekan tombol di bawah ini akan langsung merombak berkas asli di komputer Anda tanpa simulasi.
                </div>
                <div class="flex space-x-3 w-full sm:w-auto justify-end">
                    <button
                        type="submit"
                        name="action"
                        value="save_manual"
                        class="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium px-4 py-2.5 rounded-xl text-sm transition-all active:scale-95">
                        Simpan Edit Manual ke File
                    </button>
                    <button
                        type="submit"
                        name="action"
                        value="apply_patch"
                        class="bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-medium px-5 py-2.5 rounded-xl shadow-lg shadow-indigo-500/10 transition-all active:scale-95 text-sm flex items-center space-x-2">
                        <span>Eksekusi & Ubah Otomatis Ke File asli</span>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                    </button>
                </div>
            </div>
        </form>

        {% if log_status %}
        <section class="p-4 rounded-xl border {% if 'SUKSES' in log_status or 'BERHASIL' in log_status %} bg-emerald-950/30 border-emerald-500/40 text-emerald-400 {% else %} bg-rose-950/30 border-rose-500/40 text-rose-400 {% endif %} text-sm mono flex flex-col space-y-1 shadow-md whitespace-pre-wrap">
            <span class="font-bold">[LOG SYSTEM]:</span>
            <span>{{ log_status }}</span>
        </section>
        {% endif %}

        {% if diff_results %}
        <section class="space-y-3">
            <div class="flex justify-between items-center border-b border-slate-800 pb-2">
                <h3 class="text-sm font-semibold tracking-wider text-slate-400">STREAM VISUALISASI STRUKTUR PERUBAHAN (DIFF VIA DISK)</h3>
                <span class="text-xs text-slate-500 font-mono">Unified Stream Matrix</span>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
                <div class="p-4 overflow-x-auto mono text-sm leading-relaxed space-y-0.5">
                    {% for line in diff_results %}
                        {% if line.startswith('-') %}
                            <div class="bg-rose-950/40 text-rose-300 border-l-4 border-rose-500 px-2 -mx-4"><span class="opacity-40 inline-block w-4 select-none">-</span> {{ line[1:] }}</div>
                        {% elif line.startswith('+') %}
                            <div class="bg-emerald-950/40 text-emerald-300 border-l-4 border-emerald-500 px-2 -mx-4"><span class="opacity-40 inline-block w-4 select-none">+</span> {{ line[1:] }}</div>
                        {% elif line.startswith('@') %}
                            <div class="bg-cyan-950/40 text-cyan-400 font-bold px-2 -mx-4 py-0.5 border-y border-cyan-950/50 my-1 select-none">{{ line }}</div>
                        {% else %}
                            <div class="text-slate-500 px-2"><span class="opacity-10 inline-block w-4 select-none"> </span> {{ line[1:] }}</div>
                        {% endif %}
                    {% endfor %}
                </div>
            </div>
        </section>
        {% endif %}

    </main>

    <footer class="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-600 mt-auto">
        DiffKu Workstation v3 &bull; 2026 &bull; Manipulasi File Sistem Riil Tanpa Ketik Manual
    </footer>

</body>
</html>
'''

def fuzzy_sliding_window_patch(isi_asli, search_block, replace_block, threshold=0.70):
    lines_asli = [line.rstrip('\r') for line in isi_asli.splitlines()]
    lines_search = [line.rstrip('\r') for line in search_block.splitlines()]

    len_search = len(lines_search)
    if len_search == 0:
        return None, "⚠️ Blok SEARCH kosong."

    best_ratio = 0
    best_match_index = -1
    search_str_clean = "\n".join(lines_search)

    for i in range(len(lines_asli) - len_search + 1):
        window_konten = "\n".join(lines_asli[i:i+len_search])
        ratio = SequenceMatcher(None, window_konten, search_str_clean).ratio()

        if ratio > best_ratio:
            best_ratio = ratio
            best_match_index = i

    if best_ratio >= threshold:
        bagian_atas = lines_asli[:best_match_index]
        bagian_bawah = lines_asli[best_match_index+len_search:]

        lines_baru = bagian_atas + replace_block.splitlines() + bagian_bawah
        isi_baru = "\n".join(lines_baru)

        log_msg = f"✅ SUKSES mencocokkan target (Fuzzy {round(best_ratio * 100, 2)}%) mulai baris ke-{best_match_index + 1}."
        return isi_baru, log_msg
    else:
        log_msg = f"❌ GAGAL patch AI. Kecocokan terdekat hanya {round(best_ratio * 100, 2)}% (Maks Threshold {int(threshold*100)}%)."
        return None, log_msg


@app.route('/', methods=['GET', 'POST'])
def index():
    file_path = ""
    file_asli_content = ""
    ai_instruction = ""
    log_status = None
    diff_results = None

    if request.method == 'GET':
        ai_instruction = (
            "// Tempel instruksi AI di sini, contoh:\n"
            "<<<<<<< SEARCH\n"
            "def konfigurasi_sistem():\n"
            "=======\n"
            "def konfigurasi_sistem():\n"
            "    print('Mengubah konfigurasi riil...')\n"
            ">>>>>>> REPLACE"
        )

    if request.method == 'POST':
        action = request.form.get('action')
        file_path = request.form.get('file_path', '').strip()
        file_asli_content = request.form.get('file_asli_content', '')
        ai_instruction = request.form.get('ai_instruction', '')

        # AKSI 1: MEMBUKA WINDOWS NATIVE FILE EXPLORER (MILIH FILE TANPA KETIK)
        if action == 'browse_file':
            root = tk.Tk()
            root.withdraw()                       # Sembunyikan window kosong bawaan tk
            root.attributes('-topmost', True)     # Paksa pop-up muncul di urutan paling depan layar
            selected_path = filedialog.askopenfilename(
                title="Pilih File Program Utama Anda",
                filetypes=[("Python Files", "*.py"), ("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            root.destroy()                        # Tutup instansi tk setelah selesai memilih

            if selected_path:
                file_path = os.path.normpath(selected_path) # Rapikan format slash path Windows
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_asli_content = f.read()
                    log_status = f"✅ BERHASIL MEMUAT FILE! Jalur riil otomatis terhubung ke: {file_path}"
                except Exception as e:
                    log_status = f"❌ GAGAL membaca berkas file pilihan: {str(e)}"
            else:
                log_status = "⚠️ Pemilihan file dibatalkan oleh pengguna."

        # AKSI 2: SIMPAN EDIT MANUAL LANGSUNG KE DISK (OVERWRITE)
        elif action == 'save_manual':
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_asli_content)
                    log_status = f"✅ BERHASIL! Perubahan manual langsung ditulis dan disimpan ke '{file_path}'."
                except Exception as e:
                    log_status = f"❌ GAGAL menulis file ke disk: {str(e)}"
            else:
                log_status = "❌ GAGAL! File belum dipilih. Klik tombol 'Pilih File dari Komputer' dulu."

        # AKSI 3: EKSEKUSI PATCH AI & LANGSUNG TIMPA OTOMATIS KE DISK (OVERWRITE)
        elif action == 'apply_patch':
            if not file_path or not os.path.exists(file_path):
                log_status = "❌ GAGAL! Tidak ada file target yang aktif. Pilih file program Anda terlebih dahulu."
            else:
                ai_instruction_cleaned = ai_instruction.replace('\xa0', ' ')
                pattern = r"<<<<<<<\s*SEARCH[\r\n]+([\s\S]*?)[\r\n]+=======\s*[\r\n]+([\s\S]*?)[\r\n]+>>>>>>>\s*REPLACE"
                matches = list(re.finditer(pattern, ai_instruction_cleaned))

                if not matches:
                    log_status = "❌ GAGAL! Format teks AI tidak mengandung blok <<<<<<< SEARCH / ======= / >>>>>>> REPLACE."
                else:
                    patch_count = 0
                    current_file_content = file_asli_content
                    all_diffs = []
                    all_logs = []

                    for idx, match in enumerate(matches, 1):
                        search_block = match.group(1)
                        replace_block = match.group(2)

                        isi_terupdate, log_msg = fuzzy_sliding_window_patch(
                            current_file_content, search_block, replace_block
                        )

                        if isi_terupdate is not None:
                            diff = unified_diff(
                                [l.rstrip('\r') for l in current_file_content.splitlines()],
                                [l.rstrip('\r') for l in isi_terupdate.splitlines()],
                                lineterm=""
                            )
                            all_diffs.extend(list(diff)[2:])

                            current_file_content = isi_terupdate
                            patch_count += 1
                            all_logs.append(f"[Patch {idx}] {log_msg}")
                        else:
                            all_logs.append(f"[Patch {idx}] {log_msg}")
                            break

                    if patch_count > 0:
                        try:
                            # MODIFIKASI BERHASIL -> LANGSUNG TIMPA FILE ASLI DI SISTEM KORBAN/LOKAL
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(current_file_content)
                            
                            file_asli_content = current_file_content
                            diff_results = all_diffs
                            log_status = f"✅ SUKSES TOTAL! {patch_count} patch diterapkan. File '{os.path.basename(file_path)}' TELAH DIUBAH OTOMATIS di harddisk.\n" + "\n".join(all_logs)
                        except Exception as e:
                            log_status = f"❌ GAGAL menyimpan hasil patch ke dalam file asli: {str(e)}"
                    else:
                        log_status = f"❌ Tidak ada patch yang berhasil diterapkan ke file.\n" + "\n".join(all_logs)

    return render_template_string(
        HTML_TEMPLATE,
        file_path=file_path,
        file_asli=file_asli_content,
        ai_instruction=ai_instruction,
        log_status=log_status,
        diff_results=diff_results
    )

if __name__ == '__main__':
    app.run(port=5001, debug=True)
