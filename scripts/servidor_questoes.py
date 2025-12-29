#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor Web - Visualizador de Questões OAB
Interface web para navegar e testar questões
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from pathlib import Path


class ServidorQuestoes(BaseHTTPRequestHandler):
    # Banco de questões (carregado na inicialização)
    questoes = []

    def do_GET(self):
        """Handle GET requests."""
        path = urllib.parse.urlparse(self.path).path

        if path == '/' or path == '/index.html':
            self.servir_pagina_principal()
        elif path == '/api/questoes':
            self.servir_lista_questoes()
        elif path.startswith('/api/questao/'):
            numero = int(path.split('/')[-1])
            self.servir_questao_especifica(numero)
        elif path == '/api/aleatoria':
            self.servir_questao_aleatoria()
        elif path == '/api/buscar':
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            termo = params.get('q', [''])[0]
            self.servir_busca(termo)
        else:
            self.send_error(404)

    def servir_pagina_principal(self):
        """Serve HTML principal."""
        html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Banco de Questões OAB</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .stat {
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 30px;
        }
        button {
            padding: 15px 30px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102,126,234,0.4);
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #218838;
        }
        .questao-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        .questao-card.show {
            display: block;
            animation: fadeIn 0.5s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .questao-numero {
            color: #667eea;
            font-size: 0.9em;
            margin-bottom: 15px;
        }
        .questao-texto {
            font-size: 1.1em;
            line-height: 1.6;
            margin-bottom: 20px;
            color: #333;
        }
        .alternativa {
            padding: 15px;
            margin: 10px 0;
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .alternativa:hover {
            border-color: #667eea;
            transform: translateX(5px);
        }
        .alternativa.correta {
            background: #d4edda;
            border-color: #28a745;
        }
        .alternativa.incorreta {
            background: #f8d7da;
            border-color: #dc3545;
        }
        .gabarito {
            margin-top: 20px;
            padding: 15px;
            background: #d4edda;
            border-left: 4px solid #28a745;
            border-radius: 5px;
            display: none;
        }
        .gabarito.show {
            display: block;
        }
        input[type="search"] {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        input[type="search"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .loading {
            text-align: center;
            color: #667eea;
            font-size: 1.2em;
            padding: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 Banco de Questões OAB</h1>

        <div class="stats">
            <div class="stat">
                <div class="stat-number" id="total-questoes">...</div>
                <div class="stat-label">Total de Questões</div>
            </div>
            <div class="stat">
                <div class="stat-number" id="acertos">0</div>
                <div class="stat-label">Acertos</div>
            </div>
            <div class="stat">
                <div class="stat-number" id="erros">0</div>
                <div class="stat-label">Erros</div>
            </div>
        </div>

        <input type="search" id="busca" placeholder="Buscar questões...">

        <div class="controls">
            <button class="btn-primary" onclick="carregarQuestaoAleatoria()">
                🎲 Questão Aleatória
            </button>
            <button class="btn-primary" onclick="proximaQuestao()">
                ➡️ Próxima Questão
            </button>
            <button class="btn-success" onclick="mostrarGabarito()">
                ✓ Mostrar Gabarito
            </button>
            <button class="btn-success" onclick="resetarContadores()">
                🔄 Resetar Contadores
            </button>
        </div>

        <div id="questao-container" class="questao-card">
            <div class="loading">Carregando questões...</div>
        </div>
    </div>

    <script>
        let questoes = [];
        let questaoAtual = null;
        let acertos = 0;
        let erros = 0;
        let indiceAtual = 0;

        // Carregar questões ao iniciar
        fetch('/api/questoes')
            .then(r => r.json())
            .then(data => {
                questoes = data;
                document.getElementById('total-questoes').textContent = questoes.length;
                carregarQuestaoAleatoria();
            });

        function carregarQuestaoAleatoria() {
            indiceAtual = Math.floor(Math.random() * questoes.length);
            mostrarQuestao(questoes[indiceAtual]);
        }

        function proximaQuestao() {
            indiceAtual = (indiceAtual + 1) % questoes.length;
            mostrarQuestao(questoes[indiceAtual]);
        }

        function mostrarQuestao(questao) {
            questaoAtual = questao;
            const container = document.getElementById('questao-container');

            let html = `
                <div class="questao-numero">
                    Questão ${questao.numero} ${questao.fonte ? '- ' + questao.fonte : ''}
                </div>
                <div class="questao-texto">${questao.pergunta}</div>
            `;

            for (const [letra, texto] of Object.entries(questao.alternativas)) {
                html += `
                    <div class="alternativa" onclick="selecionarAlternativa('${letra}')">
                        <strong>(${letra})</strong> ${texto}
                    </div>
                `;
            }

            html += `
                <div class="gabarito" id="gabarito">
                    <strong>Gabarito: ${questao.gabarito}</strong>
                </div>
            `;

            container.innerHTML = html;
            container.classList.add('show');
        }

        function selecionarAlternativa(letra) {
            if (!questaoAtual) return;

            const alternativas = document.querySelectorAll('.alternativa');
            alternativas.forEach(alt => {
                alt.classList.remove('correta', 'incorreta');
            });

            const alternativasArray = Array.from(alternativas);
            const index = Object.keys(questaoAtual.alternativas).indexOf(letra);

            if (letra === questaoAtual.gabarito) {
                alternativasArray[index].classList.add('correta');
                acertos++;
                document.getElementById('acertos').textContent = acertos;
            } else {
                alternativasArray[index].classList.add('incorreta');
                const indexCorreto = Object.keys(questaoAtual.alternativas).indexOf(questaoAtual.gabarito);
                alternativasArray[indexCorreto].classList.add('correta');
                erros++;
                document.getElementById('erros').textContent = erros;
            }

            document.getElementById('gabarito').classList.add('show');
        }

        function mostrarGabarito() {
            document.getElementById('gabarito').classList.add('show');
        }

        function resetarContadores() {
            acertos = 0;
            erros = 0;
            document.getElementById('acertos').textContent = 0;
            document.getElementById('erros').textContent = 0;
        }

        // Busca
        document.getElementById('busca').addEventListener('input', function(e) {
            const termo = e.target.value.toLowerCase();
            if (termo.length < 3) return;

            const resultados = questoes.filter(q =>
                q.pergunta.toLowerCase().includes(termo)
            );

            if (resultados.length > 0) {
                mostrarQuestao(resultados[0]);
            }
        });
    </script>
</body>
</html>
"""

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def servir_lista_questoes(self):
        """Serve lista de questões."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()

        dados = json.dumps(self.questoes, ensure_ascii=False)
        self.wfile.write(dados.encode('utf-8'))

    def servir_questao_especifica(self, numero):
        """Serve questão específica."""
        questao = next((q for q in self.questoes if q['numero'] == numero), None)

        if questao:
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            dados = json.dumps(questao, ensure_ascii=False)
            self.wfile.write(dados.encode('utf-8'))
        else:
            self.send_error(404)

    def servir_questao_aleatoria(self):
        """Serve questão aleatória."""
        import random
        questao = random.choice(self.questoes)

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        dados = json.dumps(questao, ensure_ascii=False)
        self.wfile.write(dados.encode('utf-8'))

    def servir_busca(self, termo):
        """Busca questões."""
        resultados = [q for q in self.questoes if termo.lower() in q['pergunta'].lower()]

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        dados = json.dumps(resultados[:20], ensure_ascii=False)  # Limitar a 20 resultados
        self.wfile.write(dados.encode('utf-8'))

    def log_message(self, format, *args):
        """Suprimir logs HTTP padrão."""
        pass


def iniciar_servidor(arquivo_questoes, porta=8000):
    """Inicia servidor web."""
    # Carregar questões
    print(f"Carregando questões de: {arquivo_questoes}")

    with open(arquivo_questoes, 'r', encoding='utf-8') as f:
        ServidorQuestoes.questoes = json.load(f)

    print(f"Carregadas {len(ServidorQuestoes.questoes)} questões\n")

    # Iniciar servidor
    server = HTTPServer(('localhost', porta), ServidorQuestoes)

    print("="*80)
    print("SERVIDOR WEB INICIADO!")
    print("="*80)
    print(f"\nAcesse: http://localhost:{porta}")
    print(f"\nTotal de questões: {len(ServidorQuestoes.questoes)}")
    print("\nPressione Ctrl+C para parar o servidor\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServidor encerrado.")


if __name__ == '__main__':
    # Usar banco MASTER (melhor opção: deduplicado e consolidado)
    ARQUIVO = r"C:\Users\NFC\questoes_oab_master.json"

    # Fallback para outros arquivos se master não existir
    if not Path(ARQUIVO).exists():
        ARQUIVO = r"C:\Users\NFC\questoes_oab_todos\questoes_oab_consolidado.json"

    if not Path(ARQUIVO).exists():
        ARQUIVO = r"C:\Users\NFC\questoes_oab_final.json"

    if not Path(ARQUIVO).exists():
        print("ERRO: Nenhum arquivo de questões encontrado!")
        print("Execute primeiro o extrator de questões.")
    else:
        iniciar_servidor(ARQUIVO, porta=8000)
