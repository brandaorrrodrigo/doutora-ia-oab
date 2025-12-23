"""
JURIS_IA_CORE_V1 - EXEMPLO DE USO COMPLETO
Demonstra jornada completa de um estudante no sistema

Este exemplo mostra:
1. Sessão de estudo (1ª fase)
2. Resolução de questões
3. Prática de peças (2ª fase)
4. Acompanhamento de progresso

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
"""

import requests
import json
from datetime import datetime
from typing import Dict


# ============================================================
# CONFIGURAÇÃO
# ============================================================

API_BASE_URL = "http://localhost:8000"
ALUNO_ID = "estudante_exemplo_001"


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def print_secao(titulo: str):
    """Imprime cabeçalho de seção"""
    print("\n" + "=" * 80)
    print(f"  {titulo}")
    print("=" * 80 + "\n")


def print_resultado(data: Dict):
    """Imprime resultado formatado"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def fazer_requisicao(method: str, endpoint: str, data: Dict = None) -> Dict:
    """Faz requisição à API e retorna resposta"""
    url = f"{API_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Método não suportado: {method}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        print("❌ ERRO: API não está rodando!")
        print("   Inicie a API com: python api/api_server.py")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ ERRO HTTP: {e}")
        print(f"   Resposta: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return None


# ============================================================
# CENÁRIO 1: SESSÃO DE ESTUDO (1ª FASE)
# ============================================================

def cenario_sessao_estudo():
    """Demonstra sessão completa de estudo"""
    print_secao("CENÁRIO 1: SESSÃO DE ESTUDO - 1ª FASE OAB")

    # 1. Inicia sessão
    print("1️⃣  Iniciando sessão de estudo...")
    sessao_request = {
        "aluno_id": ALUNO_ID,
        "disciplina": "Direito Penal",
        "tipo": "drill"
    }

    sessao = fazer_requisicao("POST", "/estudo/iniciar", sessao_request)

    if not sessao or not sessao.get("success"):
        print("❌ Falha ao iniciar sessão")
        return

    print("✅ Sessão iniciada com sucesso!")
    print(f"\n📊 Informações da sessão:")
    print(f"   Perfil: {sessao['data']['perfil']}")
    print(f"   Total de questões: {sessao['data']['total_questoes']}")
    print(f"   Tipo: {sessao['data']['configuracao']['tipo']}")

    print(f"\n🧠 Estado emocional:")
    emocional = sessao['data']['estado_emocional']
    print(f"   Stress: {emocional['stress']:.2f}")
    print(f"   Motivação: {emocional['motivacao']:.2f}")
    print(f"   Confiança: {emocional['confianca']:.2f}")

    # 2. Responde primeira questão
    if sessao['data']['total_questoes'] > 0:
        print("\n2️⃣  Respondendo primeira questão...")

        primeira_questao = sessao['data']['questoes'][0]
        print(f"\n📝 Questão {primeira_questao['id']}:")
        print(f"   {primeira_questao['enunciado'][:100]}...")
        print(f"   Disciplina: {primeira_questao['disciplina']}")
        print(f"   Tópico: {primeira_questao['topico']}")

        # Simula resposta (escolhe alternativa A e leva 195 segundos)
        resposta_request = {
            "aluno_id": ALUNO_ID,
            "questao_id": primeira_questao['id'],
            "alternativa_escolhida": "A",
            "tempo_segundos": 195
        }

        resposta = fazer_requisicao("POST", "/estudo/responder", resposta_request)

        if resposta and resposta.get("success"):
            print("✅ Resposta processada!")
            print(f"\n📌 Resultado: {resposta['data']['resultado']}")
            print(f"   Nível de explicação: {resposta['data']['nivel_explicacao']}")
            print(f"   Feedback de tempo: {resposta['data']['feedback_tempo']}")

            if resposta['data'].get('proximas_acoes'):
                print(f"\n🎯 Próximas ações recomendadas:")
                for acao in resposta['data']['proximas_acoes'][:3]:
                    print(f"   [{acao['prioridade']}] {acao['tipo']}")
                    print(f"       {acao['justificativa']}")

    # 3. Finaliza sessão
    print("\n3️⃣  Finalizando sessão...")
    finalizacao = fazer_requisicao("POST", f"/estudo/finalizar/{ALUNO_ID}")

    if finalizacao and finalizacao.get("success"):
        print("✅ Sessão finalizada!")

        if finalizacao['data'].get('desempenho'):
            desemp = finalizacao['data']['desempenho']
            print(f"\n📊 Resumo do desempenho:")
            print(f"   Taxa de acerto: {desemp.get('taxa_acerto_geral', 0)}%")
            print(f"   Total de questões: {desemp.get('total_questoes', 0)}")


# ============================================================
# CENÁRIO 2: PRÁTICA DE PEÇAS (2ª FASE)
# ============================================================

def cenario_pratica_peca():
    """Demonstra prática de peça processual"""
    print_secao("CENÁRIO 2: PRÁTICA DE PEÇAS - 2ª FASE OAB")

    # 1. Inicia prática
    print("1️⃣  Iniciando prática de petição inicial...")

    enunciado = """
    João da Silva emprestou R$ 10.000,00 a Maria Souza em 01/01/2024,
    mediante contrato escrito. O pagamento deveria ocorrer em 01/06/2024.
    Maria não pagou o valor na data acordada. Elabore petição inicial
    de ação de cobrança em face de Maria Souza.
    """

    pratica_request = {
        "aluno_id": ALUNO_ID,
        "tipo_peca": "PETICAO_INICIAL_CIVEL",
        "enunciado": enunciado
    }

    pratica = fazer_requisicao("POST", "/peca/iniciar", pratica_request)

    if not pratica or not pratica.get("success"):
        print("❌ Falha ao iniciar prática")
        return

    print("✅ Prática iniciada!")
    print(f"\n📝 Tipo de peça: {pratica['data']['tipo_peca']}")
    print(f"   Tempo recomendado: {pratica['data']['tempo_recomendado_minutos']} minutos")

    print(f"\n✅ Checklist de verificação:")
    for item in pratica['data']['checklist']:
        print(f"   ☐ {item}")

    # 2. Avalia peça (exemplo simplificado)
    print("\n2️⃣  Avaliando peça escrita...")

    peca_exemplo = """
    EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA 1ª VARA CÍVEL

    JOÃO DA SILVA, brasileiro, casado, portador do CPF 123.456.789-00,
    residente na Rua A, 123, São Paulo/SP, vem, por seu advogado,
    propor AÇÃO DE COBRANÇA em face de MARIA SOUZA, brasileira,
    CPF 987.654.321-00, residente na Rua B, 456, São Paulo/SP.

    DOS FATOS

    O autor emprestou à ré a quantia de R$ 10.000,00 em 01/01/2024,
    mediante contrato de mútuo por escrito. O pagamento deveria
    ocorrer em 01/06/2024, mas a ré não honrou o compromisso.

    DO DIREITO

    O contrato de mútuo está previsto nos arts. 586 e seguintes
    do Código Civil. O não pagamento gera obrigação de restituir
    o valor acrescido de juros e correção monetária.

    DOS PEDIDOS

    Diante do exposto, requer:
    a) A citação da ré;
    b) A condenação ao pagamento de R$ 10.000,00;
    c) Juros e correção monetária;
    d) Custas processuais.

    Valor da causa: R$ 10.000,00

    São Paulo, 17 de dezembro de 2025.

    ADVOGADO JOSÉ SILVA
    OAB/SP 123456
    """

    avaliacao_request = {
        "aluno_id": ALUNO_ID,
        "tipo_peca": "PETICAO_INICIAL_CIVEL",
        "conteudo": peca_exemplo,
        "enunciado": enunciado
    }

    avaliacao = fazer_requisicao("POST", "/peca/avaliar", avaliacao_request)

    if avaliacao and avaliacao.get("success"):
        print("✅ Peça avaliada!")
        data = avaliacao['data']

        print(f"\n📊 Resultado:")
        print(f"   Nota final: {data['nota_final']:.1f}")
        print(f"   Aprovado: {'✅ SIM' if data['aprovado'] else '❌ NÃO'}")
        print(f"   Erros fatais: {data['erros_fatais']}")
        print(f"   Erros graves: {data['erros_graves']}")

        print(f"\n📈 Competências:")
        for comp, nota in data['competencias'].items():
            print(f"   {comp}: {nota:.1f}")

        if data.get('pontos_fortes'):
            print(f"\n✅ Pontos fortes:")
            for ponto in data['pontos_fortes']:
                print(f"   • {ponto}")

        if data.get('pontos_melhorar'):
            print(f"\n⚠️  Pontos a melhorar:")
            for ponto in data['pontos_melhorar'][:3]:
                print(f"   • {ponto}")


# ============================================================
# CENÁRIO 3: PAINEL DO ESTUDANTE
# ============================================================

def cenario_painel_estudante():
    """Demonstra painel de acompanhamento"""
    print_secao("CENÁRIO 3: PAINEL DO ESTUDANTE")

    # 1. Obtém painel
    print("1️⃣  Obtendo painel do estudante...")

    painel = fazer_requisicao("GET", f"/estudante/painel/{ALUNO_ID}")

    if not painel or not painel.get("success"):
        print("❌ Falha ao obter painel")
        return

    print("✅ Painel carregado!")
    data = painel['data']

    print(f"\n📊 Visão Geral:")
    visao = data['visao_geral']
    print(f"   Nível: {visao['nivel']}")
    print(f"   Taxa de acerto: {visao['taxa_acerto_geral']}%")
    print(f"   Total de questões: {visao['total_questoes']}")

    print(f"\n🧠 Memória:")
    memoria = data['memoria']
    print(f"   Total de conceitos: {memoria['total_conceitos']}")
    print(f"   Conceitos dominados: {memoria['conceitos_dominados']}")
    print(f"   Taxa de retenção: {memoria['taxa_retencao']}%")

    if data.get('proximas_revisoes'):
        print(f"\n📅 Próximas revisões:")
        for revisao in data['proximas_revisoes'][:3]:
            print(f"   • {revisao['topico']} ({revisao['disciplina']})")
            print(f"     Força: {revisao['forca_memoria']}")

    if data.get('recomendacoes'):
        print(f"\n💡 Recomendações:")
        for rec in data['recomendacoes']:
            print(f"   • {rec}")

    # 2. Obtém relatório de progresso
    print("\n2️⃣  Gerando relatório de progresso...")

    relatorio = fazer_requisicao("GET", f"/estudante/relatorio/{ALUNO_ID}?periodo=semanal")

    if relatorio and relatorio.get("success"):
        print("✅ Relatório gerado!")
        data = relatorio['data']

        print(f"\n📈 Métricas da semana:")
        metricas = data['metricas']
        print(f"   Questões resolvidas: {metricas['questoes_resolvidas']}")
        print(f"   Taxa de acerto: {metricas['taxa_acerto']}%")
        print(f"   Tempo de estudo: {metricas['tempo_total_estudo_horas']}h")

        if data.get('conquistas'):
            print(f"\n🏆 Conquistas:")
            for conquista in data['conquistas']:
                print(f"   {conquista}")

        if data.get('meta_proxima_semana'):
            print(f"\n🎯 Meta para próxima semana:")
            print(f"   {data['meta_proxima_semana']}")


# ============================================================
# CENÁRIO 4: DIAGNÓSTICO COMPLETO
# ============================================================

def cenario_diagnostico():
    """Demonstra diagnóstico completo"""
    print_secao("CENÁRIO 4: DIAGNÓSTICO COMPLETO")

    print("1️⃣  Gerando diagnóstico...")

    diagnostico = fazer_requisicao("GET", f"/diagnostico/{ALUNO_ID}")

    if not diagnostico or not diagnostico.get("success"):
        print("❌ Falha ao gerar diagnóstico")
        return

    print("✅ Diagnóstico completo gerado!")
    data = diagnostico['data']

    print(f"\n📊 Desempenho:")
    if data.get('desempenho'):
        desemp = data['desempenho']
        print(f"   Nível: {desemp.get('nivel', 'N/A')}")
        print(f"   Taxa geral: {desemp.get('taxa_acerto_geral', 0)}%")

    print(f"\n🧠 Padrões de erro:")
    if data.get('padroes_erro'):
        padroes = data['padroes_erro']
        print(f"   Tipo predominante: {padroes.get('tipo_predominante', 'N/A')}")

        if padroes.get('conceitos_deficientes'):
            print(f"\n   Conceitos deficientes:")
            for conceito in padroes['conceitos_deficientes'][:5]:
                print(f"   • {conceito}")

    print(f"\n😊 Estado emocional:")
    if data.get('estado_emocional'):
        emocional = data['estado_emocional']
        print(f"   Avaliação: {emocional.get('avaliacao', 'N/A')}")

    # 2. Análise de memória
    print("\n2️⃣  Analisando memória...")

    memoria = fazer_requisicao("GET", f"/memoria/{ALUNO_ID}")

    if memoria and memoria.get("success"):
        print("✅ Análise de memória concluída!")
        data = memoria['data']

        if data.get('alertas'):
            print(f"\n⚠️  Alertas ({len(data['alertas'])} encontrados):")
            for alerta in data['alertas'][:3]:
                print(f"   [{alerta['gravidade']}] {alerta['tipo']}")
                print(f"   {alerta['mensagem']}")


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def main():
    """Executa todos os cenários"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                  JURIS_IA - EXEMPLO COMPLETO                   ║
    ║                                                                ║
    ║  Demonstração de jornada completa de um estudante no sistema   ║
    ╚════════════════════════════════════════════════════════════════╝
    """)

    # Verifica se API está rodando
    print("Verificando conexão com a API...")
    health = fazer_requisicao("GET", "/health")

    if not health:
        print("\n❌ API não está respondendo!")
        print("   Inicie a API primeiro:")
        print("   $ cd api")
        print("   $ python api_server.py")
        return

    print("✅ API está rodando!\n")

    # Executa cenários
    try:
        cenario_sessao_estudo()
        cenario_pratica_peca()
        cenario_painel_estudante()
        cenario_diagnostico()

        print_secao("EXEMPLO COMPLETO - CONCLUÍDO")
        print("✅ Todos os cenários foram executados com sucesso!")
        print("\n📚 Próximos passos:")
        print("   1. Explore a documentação interativa: http://localhost:8000/docs")
        print("   2. Teste outros endpoints")
        print("   3. Integre com seu frontend")

    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")


if __name__ == "__main__":
    main()
