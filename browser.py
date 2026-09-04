import webview
import requests
import os
import re
import json
from datetime import datetime
from urllib.parse import quote

# ============================================================
# CONFIGURAZIONE GLOBALE
# ============================================================
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
MYBROWSER_DIR = os.path.join(DESKTOP, "Mybrowser")
os.makedirs(MYBROWSER_DIR, exist_ok=True)

# La ricerca corrente (cartella in memoria)
CURRENT_RESEARCH = datetime.now().strftime("ricerca_%Y-%m-%d_%H-%M-%S")
MEMORIA_DIR = os.path.join(MYBROWSER_DIR, CURRENT_RESEARCH)
# Il diario è globale, non si azzera con le nuove ricerche
DIARIO_FILE = os.path.join(MYBROWSER_DIR, "diario_globale.json")

os.makedirs(MEMORIA_DIR, exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELLO = "qwen2.5:1.5b"

SITI_FAMOSI = {
    "google": "https://www.google.com", "youtube": "https://www.youtube.com",
    "wikipedia": "https://it.wikipedia.org", "wiki": "https://it.wikipedia.org",
    "facebook": "https://www.facebook.com", "twitter": "https://twitter.com",
    "x": "https://x.com", "reddit": "https://www.reddit.com",
    "github": "https://github.com", "amazon": "https://www.amazon.it",
    "bing": "https://www.bing.com", "duckduckgo": "https://duckduckgo.com",
    "netflix": "https://www.netflix.com",
}

# ============================================================
# FUNZIONI UTILI
# ============================================================
def crea_nome_file_sicuro(url):
    nome = url.replace("https://", "").replace("http://", "")
    nome = re.sub(r'[<>:"/\\|?*]', "_", nome)
    return nome[:60]

def pulisci_testo(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def load_diario():
    if os.path.exists(DIARIO_FILE):
        try:
            with open(DIARIO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_diario(data):
    with open(DIARIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ============================================================
# API PYWEBVIEW
# ============================================================
class Api:
    def go_home(self):
        window.load_url("https://duckduckgo.com")
        return "ok"

    def navigate(self, url):
        url = url.strip()
        if not url: return "ok"
        url_lower = url.lower()
        if url_lower in SITI_FAMOSI:
            window.load_url(SITI_FAMOSI[url_lower])
            return "ok"
        if url.startswith("http://") or url.startswith("https://") or "." in url.split("/")[0]:
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "https://" + url
            window.load_url(url)
            return "ok"
        window.load_url("https://duckduckgo.com/?q=" + quote(url))
        return "ok"

    def go_back(self):
        window.evaluate_js("history.back()")
        return "ok"

    def go_forward(self):
        window.evaluate_js("history.forward()")
        return "ok"

    def reload_page(self):
        window.evaluate_js("location.reload()")
        return "ok"

    def get_current_research(self):
        return CURRENT_RESEARCH

    def new_research(self):
        global CURRENT_RESEARCH, MEMORIA_DIR
        CURRENT_RESEARCH = datetime.now().strftime("ricerca_%Y-%m-%d_%H-%M-%S")
        MEMORIA_DIR = os.path.join(MYBROWSER_DIR, CURRENT_RESEARCH)
        os.makedirs(MEMORIA_DIR, exist_ok=True)
        return f"Nuova ricerca creata: {CURRENT_RESEARCH}. Le prossime analisi finiranno in questa cartella."

    def get_researches(self):
        researches = []
        for item in os.listdir(MYBROWSER_DIR):
            if item.startswith("ricerca_") and os.path.isdir(os.path.join(MYBROWSER_DIR, item)):
                researches.append(item)
        return sorted(researches, reverse=True)

    def add_diario_entry(self, url, title):
        data = load_diario()
        if data and data[-1].get('url') == url:
            return "ok"
        entry = {
            "url": url, 
            "title": title or "Pagina senza titolo", 
            "time": datetime.now().strftime("%d/%m %H:%M"), 
            "analyzed": False,
            "research": CURRENT_RESEARCH
        }
        data.append(entry)
        if len(data) > 300: data = data[-300:]
        save_diario(data)
        return "ok"

    def get_diario(self):
        return load_diario()

    def mark_diario_analyzed(self, url):
        data = load_diario()
        for entry in reversed(data):
            if entry['url'] == url:
                entry['analyzed'] = True
                break
        save_diario(data)
        return "ok"

    def analyze_page(self, url, text, highlights):
        try:
            text = pulisci_testo(text)
            short_text = text[:10000]
            if len(short_text.strip()) < 100:
                return "Non ho trovato abbastanza testo. Scorri la pagina prima di analizzare."

            if highlights and len(highlights) > 0:
                highlights_text = "\n".join([f"- {h}" for h in highlights[:10]])
                focus_instruction = f"""

PRIORITA ASSOLUTA: L utente ha EVIDENZIATO manualmente le seguenti parti del testo. Queste sono le informazioni piu importanti per lui. Devi includerle TUTTE nell analisi e dar loro il massimo peso:
{highlights_text}

Cerca nel resto del testo anche informazioni correlate a questi punti evidenziati."""
            else:
                focus_instruction = ""

            prompt = f"""Leggi questo testo estratto da una pagina web.
REGOLA: Ignora banner cookie, menu, footer e pubblicita. Concentrati sul contenuto reale.{focus_instruction}

Cerca ATTENTAMENTE: prezzi (euro), metri quadri (mq, m2), vani, indirizzi, nomi, date.

Rispondi ESATTAMENTE con questa struttura:
RIASSUNTO: Max 3 frasi sul contenuto reale.
DATI CHIAVE: Elenca TUTTI i prezzi, mq, luoghi o fatti trovati. Se non ci sono, scrivi "Nessun dato numerico rilevante".
CONCETTI: Max 3 punti essenziali.

TESTO:
{short_text}"""

            response = requests.post(OLLAMA_URL, json={"model": MODELLO, "prompt": prompt, "stream": False}, timeout=600)
            response.raise_for_status()
            result = response.json().get("response", "Errore: nessuna risposta.")

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{timestamp}_{crea_nome_file_sicuro(url)}.txt"
            filepath = os.path.join(MEMORIA_DIR, filename)

            with open(filepath, "w", encoding="utf-8") as file:
                file.write(f"SITO: {url}\nDATA: {datetime.now().strftime('%d/%m/%Y alle %H:%M')}\n")
                file.write(f"RICERCA: {CURRENT_RESEARCH}\n")
                file.write(f"EVIDENZIAZIONI UTENTE: {highlights}\n" + "=" * 60 + "\n\nANALISI IA\n\n")
                file.write(result)
                file.write("\n\n" + "=" * 60 + "\n\nESTRATTO TESTO:\n" + short_text[:1000] + "...")

            self.mark_diario_analyzed(url)
            return f"{result}\n\nSalvato in: {CURRENT_RESEARCH}/{filename}"

        except requests.exceptions.ConnectionError:
            return "Impossibile connettersi a Ollama."
        except requests.exceptions.Timeout:
            return "Il modello sta impiegando molto tempo. Attendi."
        except Exception as e:
            return f"Errore: {str(e)}"

    def generate_report(self):
        try:
            files = [f for f in os.listdir(MEMORIA_DIR) if f.endswith('.txt') and not f.startswith('resoconto_')]
            if not files:
                return f"Nessuna analisi salvata nella ricerca corrente ({CURRENT_RESEARCH}). Analizza prima qualche pagina."
            
            files.sort(reverse=True)
            recent_files = files[:8]
            
            summaries = []
            for f in recent_files:
                filepath = os.path.join(MEMORIA_DIR, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    idx = content.find("ANALISI IA")
                    if idx != -1:
                        snippet = content[idx:idx+1500]
                        summaries.append(f"--- {f.replace('.txt', '').replace('_', ' ')} ---\n{snippet}")
                    else:
                        summaries.append(f"--- {f} ---\n{content[:800]}")
            
            combined_text = "\n\n".join(summaries)
            
            prompt = f"""Sei un assistente di ricerca esperto.
Ecco i riassunti di diverse pagine web analizzate nella ricerca "{CURRENT_RESEARCH}".

REGOLA: Ignora cookie, privacy, banner. Concentrati sui temi sostanziali.

Fai un RESOCONTO GENERALE che:
1. Identifica i 2-3 TEMI PRINCIPALI reali.
2. Elenca le INFORMAZIONI PIU IMPORTANTI (PREZZI, LUOGHI, MQ, EVENTI).
3. Suggerisci eventuali COLLEGAMENTI tra le diverse pagine.

TESTI:
{combined_text}"""

            response = requests.post(OLLAMA_URL, json={"model": MODELLO, "prompt": prompt, "stream": False}, timeout=600)
            response.raise_for_status()
            result = response.json().get("response", "Errore nel generare il resoconto.")
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"resoconto_{timestamp}.txt"
            filepath = os.path.join(MEMORIA_DIR, filename)
            
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(f"RESOCONTO GENERALE\n")
                file.write(f"RICERCA: {CURRENT_RESEARCH}\n")
                file.write(f"DATA: {datetime.now().strftime('%d/%m/%Y alle %H:%M')}\n")
                file.write("=" * 60 + "\n\n")
                file.write(result)
                file.write("\n\n" + "=" * 60 + "\n\nRICERCHE ANALIZZATE:\n\n")
                for f in recent_files:
                    file.write(f"- {f}\n")
            
            return f"{result}\n\nResoconto salvato in: {CURRENT_RESEARCH}/{filename}"
            
        except Exception as e:
            return f"Errore: {str(e)}"

    def ask_research(self, research_name, question):
        try:
            research_dir = os.path.join(MYBROWSER_DIR, research_name)
            files = [f for f in os.listdir(research_dir) if f.endswith('.txt')]
            if not files:
                return "Questa ricerca non contiene analisi."
            
            context = ""
            for f in files[:10]:
                with open(os.path.join(research_dir, f), 'r', encoding='utf-8') as file:
                    content = file.read()
                    idx = content.find("ANALISI IA")
                    context += f"--- {f} ---\n{content[idx:idx+1500] if idx != -1 else content[:800]}\n\n"

            prompt = f"""Sei un assistente esperto. L utente ti fa una domanda basandosi sui dati salvati nella ricerca "{research_name}".
Rispondi basandoti SOLO su queste informazioni. Se la risposta non e nei dati, dillo chiaramente.

DOMANDA DELL UTENTE: {question}

DATI DELLA RICERCA:
{context}"""

            response = requests.post(OLLAMA_URL, json={"model": MODELLO, "prompt": prompt, "stream": False}, timeout=600)
            response.raise_for_status()
            return response.json().get("response", "Errore nella risposta.")
        except Exception as e:
            return f"Errore: {str(e)}"

# ============================================================
# JAVASCRIPT E UI
# ============================================================
def on_loaded():
    js = """
    (function() {
        if (document.getElementById('my-toolbar')) return;
        
        window.myHighlights = window.myHighlights || [];
        
        var t = document.createElement('div');
        t.id = 'my-toolbar';
        t.style.cssText = 'position:fixed;top:0;left:0;right:0;display:flex;align-items:center;gap:6px;padding:8px;background:#2b2b2b;z-index:999999;box-shadow:0 2px 10px rgba(0,0,0,0.4);flex-wrap:wrap;';
        t.innerHTML = `
            <button onclick="pywebview.api.go_home()" style="padding:6px 10px;cursor:pointer;background:#FF9800;color:white;border:none;border-radius:5px;font-weight:bold;">Home</button>
            <button onclick="pywebview.api.go_back()" style="padding:6px 10px;cursor:pointer;">Indietro</button>
            <button onclick="pywebview.api.go_forward()" style="padding:6px 10px;cursor:pointer;">Avanti</button>
            <button onclick="pywebview.api.reload_page()" style="padding:6px 10px;cursor:pointer;">Ricarica</button>
            <input id="my-url" type="text" value="${location.href}" style="flex:1;min-width:200px;padding:7px;font-size:14px;border-radius:5px;border:1px solid #555;" />
            <button id="go-button" style="padding:7px 12px;cursor:pointer;">Vai</button>
            <button id="highlight-button" style="padding:7px 12px;cursor:pointer;background:#FFEB3B;color:#000;border:none;border-radius:5px;font-weight:bold;">Marker</button>
            <button id="clear-highlight-button" style="padding:7px 12px;cursor:pointer;background:#F44336;color:white;border:none;border-radius:5px;">Pulisci Marker</button>
            <button id="diario-button" style="padding:7px 12px;cursor:pointer;background:#2196F3;color:white;border:none;border-radius:5px;">Diario</button>
            <button id="report-button" style="padding:7px 12px;cursor:pointer;background:#9C27B0;color:white;border:none;border-radius:5px;font-weight:bold;">Resoconto</button>
            <button id="ask-button" style="padding:7px 12px;cursor:pointer;background:#673AB7;color:white;border:none;border-radius:5px;">Chiedi</button>
            <button id="new-research-button" style="padding:7px 12px;cursor:pointer;background:#607D8B;color:white;border:none;border-radius:5px;">Nuova Ricerca</button>
            <button id="ai-button" style="padding:7px 12px;cursor:pointer;background:#4CAF50;color:white;border:none;border-radius:5px;font-weight:bold;">Analizza</button>
        `;
        document.body.style.marginTop = '55px';
        document.body.insertBefore(t, document.body.firstChild);

        // Badge ricerca corrente
        var researchBadge = document.createElement('div');
        researchBadge.id = 'research-badge';
        researchBadge.style.cssText = 'position:fixed;top:55px;left:0;right:0;padding:4px 10px;background:#37474F;color:#B0BEC5;font-size:11px;z-index:999998;border-bottom:1px solid #455A64;';
        pywebview.api.get_current_research().then(name => {
            researchBadge.textContent = 'Ricerca attiva: ' + name;
        });
        document.body.appendChild(researchBadge);
        document.body.style.marginTop = '75px';

        var sidebar = document.createElement('div');
        sidebar.id = 'diario-sidebar';
        sidebar.style.cssText = 'display:none; position:fixed; top:75px; right:0; bottom:0; width:320px; background:#1e1e1e; color:#e0e0e0; border-left:1px solid #444; z-index:999998; padding:15px; overflow-y:auto; box-shadow:-4px 0 15px rgba(0,0,0,0.5);';
        sidebar.innerHTML = `
            <div style="font-weight:bold; font-size:16px; margin-bottom:10px; color:#2196F3;">DIARIO GLOBALE</div>
            <input type="text" id="diario-search" placeholder="Cerca..." oninput="renderDiario(this.value)" style="width:100%; padding:8px; margin-bottom:15px; border-radius:5px; border:1px solid #555; background:#2b2b2b; color:white; box-sizing:border-box;" />
            <div id="diario-list"></div>
        `;
        document.body.appendChild(sidebar);

        var askModal = document.createElement('div');
        askModal.id = 'ask-modal';
        askModal.style.cssText = 'display:none; position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); width:500px; background:#1e1e1e; color:#e0e0e0; border:1px solid #673AB7; border-radius:10px; padding:20px; z-index:1000000; box-shadow:0 10px 30px rgba(0,0,0,0.8);';
        askModal.innerHTML = `
            <div style="font-weight:bold; font-size:18px; margin-bottom:15px; color:#673AB7;">Chiedi ai Dati di una Ricerca</div>
            <label style="font-size:12px; color:#aaa;">Seleziona Ricerca:</label>
            <select id="ask-research-select" style="width:100%; padding:8px; margin-bottom:10px; background:#2b2b2b; color:white; border:1px solid #555; border-radius:5px;"></select>
            <label style="font-size:12px; color:#aaa;">La tua domanda:</label>
            <textarea id="ask-question" rows="4" style="width:100%; padding:8px; margin-bottom:15px; background:#2b2b2b; color:white; border:1px solid #555; border-radius:5px; resize:vertical;" placeholder="Es: Quali erano i prezzi delle case a Siena?"></textarea>
            <div style="display:flex; gap:10px; justify-content:flex-end;">
                <button id="ask-close" style="padding:8px 16px; cursor:pointer; background:#333; color:white; border:1px solid #555; border-radius:5px;">Chiudi</button>
                <button id="ask-send" style="padding:8px 16px; cursor:pointer; background:#673AB7; color:white; border:none; border-radius:5px; font-weight:bold;">Invia all IA</button>
            </div>
            <div id="ask-result" style="margin-top:15px; padding:10px; background:#2b2b2b; border-radius:5px; display:none; max-height:300px; overflow-y:auto; white-space:pre-wrap; font-size:13px;"></div>
        `;
        document.body.appendChild(askModal);

        document.getElementById('my-url').addEventListener('keypress', e => { if(e.key==='Enter') pywebview.api.navigate(e.target.value); });
        document.getElementById('go-button').addEventListener('click', () => pywebview.api.navigate(document.getElementById('my-url').value));
        document.getElementById('diario-button').addEventListener('click', toggleDiario);
        document.getElementById('new-research-button').addEventListener('click', newResearch);
        document.getElementById('report-button').addEventListener('click', generateReport);
        document.getElementById('ask-button').addEventListener('click', openAskModal);
        document.getElementById('ask-close').addEventListener('click', () => { askModal.style.display='none'; });
        document.getElementById('ask-send').addEventListener('click', sendAsk);
        document.getElementById('highlight-button').addEventListener('click', highlightSelection);
        document.getElementById('clear-highlight-button').addEventListener('click', clearHighlights);
        document.getElementById('ai-button').addEventListener('click', analyze);

        function escapeHtml(text) { var d=document.createElement('div'); d.textContent=text; return d.innerHTML; }

        function highlightSelection() {
            var selection = window.getSelection();
            if (!selection || selection.isCollapsed) {
                alert("Prima seleziona il testo con il mouse che vuoi evidenziare!");
                return;
            }
            var selectedText = selection.toString().trim();
            if (selectedText.length < 3) {
                alert("Selezione troppo corta. Seleziona almeno una frase.");
                return;
            }
            var range = selection.getRangeAt(0);
            var mark = document.createElement('mark');
            mark.className = 'user-highlight';
            mark.style.cssText = 'background:#FFEB3B !important; color:#000 !important; padding:2px 0; border-radius:3px;';
            try {
                range.surroundContents(mark);
            } catch(e) {
                var fragment = range.extractContents();
                mark.appendChild(fragment);
                range.insertNode(mark);
            }
            window.myHighlights.push(selectedText);
            selection.removeAllRanges();
            var btn = document.getElementById('highlight-button');
            btn.style.background = '#4CAF50';
            setTimeout(() => { btn.style.background = '#FFEB3B'; }, 300);
        }

        function clearHighlights() {
            var marks = document.querySelectorAll('mark.user-highlight');
            marks.forEach(mark => {
                var parent = mark.parentNode;
                while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
                parent.removeChild(mark);
            });
            window.myHighlights = [];
        }

        function toggleDiario() {
            var sb = document.getElementById('diario-sidebar');
            sb.style.display = (sb.style.display === 'none' || sb.style.display === '') ? 'block' : 'none';
            if(sb.style.display === 'block') renderDiario('');
        }

        function renderDiario(filter) {
            pywebview.api.get_diario().then(entries => {
                var list = document.getElementById('diario-list');
                list.innerHTML = '';
                var filtered = entries.filter(e => e.title.toLowerCase().includes(filter.toLowerCase()) || e.url.toLowerCase().includes(filter.toLowerCase()));
                filtered.reverse().forEach(e => {
                    var div = document.createElement('div');
                    div.style.cssText = 'padding:12px; border-bottom:1px solid #333; cursor:pointer; transition:background 0.2s; border-radius:5px; margin-bottom:5px;';
                    div.onmouseover = () => div.style.background = '#333';
                    div.onmouseout = () => div.style.background = 'transparent';
                    div.onclick = () => { pywebview.api.navigate(e.url); document.getElementById('diario-sidebar').style.display = 'none'; };
                    var researchLabel = e.research ? '<div style="font-size:10px; color:#555;">' + e.research + '</div>' : '';
                    div.innerHTML = `<div style="font-weight:bold; color:#4CAF50; font-size:14px; margin-bottom:4px;">${e.analyzed ? '[IA]' : '[*]'} ${escapeHtml(e.title)}</div>
                                     <div style="font-size:12px; color:#aaa; word-break:break-all;">${escapeHtml(e.url)}</div>
                                     ${researchLabel}
                                     <div style="font-size:11px; color:#666;">${e.time}</div>`;
                    list.appendChild(div);
                });
                if(filtered.length === 0) list.innerHTML = '<div style="color:#666; text-align:center; padding:20px;">Nessuna voce.</div>';
            });
        }

        function newResearch() {
            var name = prompt("Dai un nome a questa nuova ricerca (opzionale, lascia vuoto per nome automatico):");
            if(name === null) return; // Annullato
            pywebview.api.new_research().then(res => {
                alert(res);
                document.getElementById('research-badge').textContent = 'Ricerca attiva: ' + res.split(': ')[1];
                window.myHighlights = [];
            });
        }

        function openAskModal() {
            pywebview.api.get_researches().then(researches => {
                var select = document.getElementById('ask-research-select');
                select.innerHTML = '';
                if(researches.length === 0) {
                    alert("Nessuna ricerca trovata. Fai prima qualche analisi!");
                    return;
                }
                researches.forEach(r => {
                    var opt = document.createElement('option');
                    opt.value = r; opt.textContent = r;
                    select.appendChild(opt);
                });
                document.getElementById('ask-question').value = '';
                document.getElementById('ask-result').style.display = 'none';
                document.getElementById('ask-modal').style.display = 'block';
            });
        }

        function sendAsk() {
            var research = document.getElementById('ask-research-select').value;
            var question = document.getElementById('ask-question').value;
            if(!question) return alert("Scrivi una domanda!");
            var resDiv = document.getElementById('ask-result');
            resDiv.style.display = 'block';
            resDiv.innerHTML = '<b style="color:#673AB7;">L IA sta leggendo la ricerca...</b>';
            pywebview.api.ask_research(research, question).then(response => {
                resDiv.innerHTML = escapeHtml(response).replace(/\\n/g, '<br>');
            }).catch(err => {
                resDiv.innerHTML = '<b style="color:red;">Errore:</b> ' + err;
            });
        }

        function generateReport() {
            var resultDiv = document.getElementById('ia-result');
            if (!resultDiv) {
                resultDiv = document.createElement('div');
                resultDiv.id = 'ia-result';
                resultDiv.style.cssText = 'position:fixed;bottom:20px;right:20px;width:450px;max-height:600px;overflow-y:auto;background:#1e1e1e;color:#e0e0e0;border:1px solid #9C27B0;padding:16px;border-radius:10px;box-shadow:0 4px 18px rgba(0,0,0,0.6);z-index:999999;font-family:Arial,sans-serif;font-size:14px;line-height:1.5;';
                document.body.appendChild(resultDiv);
            }
            resultDiv.innerHTML = '<b style="color:#9C27B0;">Generazione Resoconto in corso...</b><br><br>Sto leggendo tutte le analisi della ricerca corrente.';
            resultDiv.style.display = 'block';

            pywebview.api.generate_report().then(response => {
                resultDiv.innerHTML = '';
                var title = document.createElement('div');
                title.textContent = 'RESOCONTO GENERALE';
                title.style.cssText = 'color:#9C27B0;font-weight:bold;font-size:16px;margin-bottom:12px;';
                var content = document.createElement('div');
                content.textContent = response;
                content.style.whiteSpace = 'pre-wrap';
                var closeButton = document.createElement('button');
                closeButton.textContent = 'Chiudi';
                closeButton.style.cssText = 'margin-top:15px;padding:6px 12px;cursor:pointer;background:#333;color:white;border:1px solid #555;border-radius:5px;';
                closeButton.onclick = () => resultDiv.style.display = 'none';
                resultDiv.appendChild(title);
                resultDiv.appendChild(content);
                resultDiv.appendChild(closeButton);
            }).catch(error => {
                resultDiv.innerHTML = '<b style="color:red;">Errore:</b><br>' + error;
            });
        }

        function analyze() {
            var mainContent = document.querySelector('main') || document.querySelector('article') || document.querySelector('#content') || document.body;
            var clone = mainContent.cloneNode(true);
            clone.querySelectorAll('script, style, nav, footer, header, iframe, noscript, .cookie-banner, .banner').forEach(el => el.remove());

            var resultDiv = document.getElementById('ia-result');
            if (!resultDiv) {
                resultDiv = document.createElement('div');
                resultDiv.id = 'ia-result';
                resultDiv.style.cssText = 'position:fixed;bottom:20px;right:20px;width:400px;max-height:500px;overflow-y:auto;background:#1e1e1e;color:#e0e0e0;border:1px solid #4CAF50;padding:16px;border-radius:10px;box-shadow:0 4px 18px rgba(0,0,0,0.6);z-index:999999;font-family:Arial,sans-serif;font-size:14px;line-height:1.5;';
                document.body.appendChild(resultDiv);
            }

            var highlightCount = window.myHighlights.length;
            var msg = highlightCount > 0 
                ? `Analisi in corso... (${highlightCount} parti evidenziate come prioritarie)` 
                : 'Analisi in corso... Il modello sta leggendo la pagina.';
            resultDiv.innerHTML = `<b style="color:#4CAF50;">${msg}</b>`;
            resultDiv.style.display = 'block';

            pywebview.api.analyze_page(location.href, clone.innerText, window.myHighlights).then(response => {
                resultDiv.innerHTML = '';
                var title = document.createElement('div');
                title.textContent = 'RISULTATO IA';
                title.style.cssText = 'color:#4CAF50;font-weight:bold;font-size:16px;margin-bottom:12px;';
                var content = document.createElement('div');
                content.textContent = response;
                content.style.whiteSpace = 'pre-wrap';
                var closeButton = document.createElement('button');
                closeButton.textContent = 'Chiudi';
                closeButton.style.cssText = 'margin-top:15px;padding:6px 12px;cursor:pointer;background:#333;color:white;border:1px solid #555;border-radius:5px;';
                closeButton.onclick = () => resultDiv.style.display = 'none';
                resultDiv.appendChild(title);
                resultDiv.appendChild(content);
                resultDiv.appendChild(closeButton);
                if (document.getElementById('diario-sidebar').style.display === 'block') renderDiario('');
            }).catch(error => {
                resultDiv.innerHTML = '<b style="color:red;">Errore:</b><br>' + error;
            });
        }

        pywebview.api.add_diario_entry(location.href, document.title);
    })();
    """
    window.evaluate_js(js)

# ============================================================
# CREAZIONE FINESTRA
# ============================================================
window = webview.create_window(
    "Browser con Memoria IA e Ricerche",
    url="https://duckduckgo.com",
    js_api=Api(),
    text_select=True,
    width=1200,
    height=800
)

window.events.loaded += on_loaded
webview.start()
