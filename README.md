# Browser con Memoria IA Locale

Un browser web sperimentale che integra intelligenza artificiale locale per analizzare, ricordare e collegare le informazioni che trovi online.

## Caratteristiche

- **Analisi IA Locale**: Usa Ollama con modelli open source (Qwen 2.5) per analizzare le pagine web senza inviare dati a server esterni
- **Evidenziatore Intelligente**: Seleziona e marca le parti importanti delle pagine, l'IA darà loro priorità assoluta
- **Memoria a Lungo Termine**: Ogni analisi viene salvata in cartelle organizzate per "ricerca tematica"
- **Resoconti Automatici**: Genera sintesi collegando tutte le pagine analizzate in una ricerca
- **Chiedi ai Dati**: Interroga l'IA su ricerche specifiche per recuperare informazioni passate
- **Diario Globale**: Cronologia completa di tutte le pagine visitate
- **Privacy Totale**: Tutto gira localmente sul tuo PC, nessun dato viene inviato al cloud

## Requisiti

- Python 3.12+
- Ollama installato e avviato
- Modello Qwen 2.5 (1.5b o 3b consigliato)

## Installazione

1. Installa Ollama da https://ollama.com
2. Scarica il modello:
   ```bash
   ollama pull qwen2.5:1.5b



MIT License
Copyright (c) 2026
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.