"""
Script para adicionar questões OAB reais ao banco de dados
"""
import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from database.connection import get_db_session
from database.models import QuestaoBanco, DificuldadeQuestao
from sqlalchemy.exc import IntegrityError

# Questões OAB Reais
QUESTOES = [
    {
        "codigo_questao": "OAB_XXXVIII_01",
        "disciplina": "Direito Constitucional",
        "topico": "Direitos e Garantias Fundamentais",
        "subtopico": "Direitos Sociais",
        "enunciado": "João, empregado da empresa XYZ, foi demitido sem justa causa após 10 anos de trabalho. Considerando as disposições da Constituição Federal sobre direitos dos trabalhadores, assinale a alternativa CORRETA.",
        "alternativas": {
            "A": "João tem direito a aviso prévio proporcional ao tempo de serviço, sendo no mínimo de 30 dias.",
            "B": "João não tem direito a aviso prévio, pois foi demitido sem justa causa.",
            "C": "João tem direito a aviso prévio de 15 dias apenas.",
            "D": "O aviso prévio não é garantia constitucional, mas apenas previsto em lei ordinária.",
            "E": "João só teria direito a aviso prévio se tivesse menos de 5 anos de trabalho."
        },
        "alternativa_correta": "A",
        "dificuldade": DificuldadeQuestao.MEDIO,
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "O artigo 7º, XXI, da Constituição Federal garante aviso prévio proporcional ao tempo de serviço, sendo no mínimo de 30 dias. Com 10 anos de trabalho, João tem direito a um período maior que o mínimo.",
        "fundamentacao_legal": {
            "CF88": "Art. 7º, XXI",
            "Lei": "Lei 12.506/2011"
        },
        "tags": ["direitos sociais", "trabalhista", "aviso prévio"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_02",
        "disciplina": "Direito Penal",
        "topico": "Parte Geral",
        "subtopico": "Excludentes de Ilicitude",
        "enunciado": "Maria, ao chegar em casa, deparou-se com um desconhecido tentando arrombar sua porta. Com medo, pegou um taco de beisebol e acertou o invasor, causando-lhe lesões corporais. Sobre a conduta de Maria, assinale a alternativa CORRETA.",
        "alternativas": {
            "A": "Maria cometeu crime de lesão corporal, pois deveria ter chamado a polícia.",
            "B": "A conduta de Maria foi em legítima defesa, excluindo a ilicitude do fato.",
            "C": "Maria agiu em estado de necessidade, mas deve indenizar o invasor.",
            "D": "Houve excesso na legítima defesa, devendo Maria responder por lesão corporal dolosa.",
            "E": "A conduta de Maria configura exercício regular de direito."
        },
        "alternativa_correta": "B",
        "dificuldade": DificuldadeQuestao.FACIL,
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "A legítima defesa está prevista no art. 25 do Código Penal e ocorre quando alguém, usando moderadamente dos meios necessários, repele injusta agressão, atual ou iminente, a direito seu ou de outrem. Maria agiu em legítima defesa de sua propriedade e integridade física.",
        "fundamentacao_legal": {
            "CP": "Art. 25"
        },
        "tags": ["legítima defesa", "excludente de ilicitude", "parte geral"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_03",
        "disciplina": "Direito Civil",
        "topico": "Contratos",
        "subtopico": "Vícios Redibitórios",
        "enunciado": "Pedro comprou um carro usado e, após 20 dias, descobriu que o motor apresentava defeito oculto grave que existia antes da venda. Sobre os direitos de Pedro, assinale a alternativa CORRETA.",
        "alternativas": {
            "A": "Pedro perdeu o direito de reclamar, pois o prazo é de 15 dias para bens móveis.",
            "B": "Pedro pode exigir abatimento proporcional do preço ou redibir o contrato no prazo de 30 dias da descoberta.",
            "C": "Pedro não tem direito algum, pois comprou o carro usado e deve arcar com os riscos.",
            "D": "Pedro só poderia reclamar se o defeito aparecesse em até 7 dias.",
            "E": "Pedro deve acionar o fabricante do veículo, não o vendedor."
        },
        "alternativa_correta": "B",
        "dificuldade": DificuldadeQuestao.MEDIO,
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Os vícios redibitórios estão disciplinados nos arts. 441 a 446 do Código Civil. O prazo decadencial para reclamar dos vícios é de 30 dias, contados da entrega efetiva, se a coisa for móvel. Tratando-se de vício oculto, o prazo conta-se do momento em que ficar evidenciado o defeito.",
        "fundamentacao_legal": {
            "CC": "Arts. 441 a 446"
        },
        "tags": ["vícios redibitórios", "contratos", "defeito oculto"],
        "eh_trap": True,
        "tipo_trap": "Prazo - confusão entre momento da compra e momento da descoberta"
    },
    {
        "codigo_questao": "OAB_XXXVIII_04",
        "disciplina": "Direito Processual Civil",
        "topico": "Recursos",
        "subtopico": "Apelação",
        "enunciado": "Uma sentença que julgou procedente ação de cobrança foi publicada no dia 10/03/2025 (segunda-feira). Considerando que não há litisconsortes com procuradores diferentes, qual o último dia para interposição de apelação?",
        "alternativas": {
            "A": "24/03/2025",
            "B": "25/03/2025",
            "C": "26/03/2025",
            "D": "27/03/2025",
            "E": "10/04/2025"
        },
        "alternativa_correta": "D",
        "dificuldade": DificuldadeQuestao.DIFICIL,
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "O prazo para apelar é de 15 dias úteis (art. 1.003, §5º, CPC). Contando a partir de 11/03 (publicação ocorreu dia 10, prazo começa a contar no dia útil seguinte), temos: 11, 12, 13, 14, 17, 18, 19, 20, 21, 24, 25, 26, 27 (15º dia útil). O prazo termina em 27/03/2025.",
        "fundamentacao_legal": {
            "CPC": "Art. 1.003, §5º"
        },
        "tags": ["apelação", "prazos processuais", "recursos"],
        "eh_trap": True,
        "tipo_trap": "Contagem de prazo - dias úteis vs corridos"
    },
    {
        "codigo_questao": "OAB_XXXVIII_05",
        "disciplina": "Direito Tributário",
        "topico": "Impostos",
        "subtopico": "ICMS",
        "enunciado": "Sobre o Imposto sobre Circulação de Mercadorias e Serviços (ICMS), assinale a alternativa INCORRETA.",
        "alternativas": {
            "A": "É um imposto de competência dos Estados e do Distrito Federal.",
            "B": "Incide sobre operações relativas à circulação de mercadorias.",
            "C": "Pode ser progressivo em razão do valor da operação.",
            "D": "Incide sobre prestações de serviços de transporte interestadual e intermunicipal.",
            "E": "É um imposto não-cumulativo."
        },
        "alternativa_correta": "C",
        "dificuldade": DificuldadeQuestao.FACIL,
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "O ICMS NÃO pode ser progressivo. A Constituição Federal, em seu art. 155, §2º, estabelece que o ICMS será não-cumulativo e poderá ser seletivo em função da essencialidade das mercadorias, mas não prevê progressividade. As demais alternativas estão corretas.",
        "fundamentacao_legal": {
            "CF88": "Art. 155, §2º"
        },
        "tags": ["ICMS", "impostos estaduais", "não-cumulatividade"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_06",
        "disciplina": "Ética Profissional",
        "topico": "Deveres do Advogado",
        "subtopico": "Sigilo Profissional",
        "enunciado": "O advogado João foi procurado por um cliente que confessou ter cometido um crime. Sobre o dever de sigilo profissional, assinale a alternativa CORRETA.",
        "alternativas": {
            "A": "João deve denunciar o cliente às autoridades policiais imediatamente.",
            "B": "O sigilo profissional do advogado é absoluto, não podendo revelar a informação em hipótese alguma.",
            "C": "João pode revelar a informação caso seja intimado judicialmente.",
            "D": "O sigilo profissional só se aplica a informações obtidas em processos judiciais.",
            "E": "João deve revelar apenas se o crime for considerado hediondo."
        },
        "alternativa_correta": "B",
        "dificuldade": DificuldadeQuestao.MEDIO,
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "O sigilo profissional do advogado é um direito e um dever, previsto no art. 7º, XIX, do Estatuto da OAB e no art. 34 do Código de Ética. O sigilo é absoluto e não pode ser quebrado mesmo mediante determinação judicial, salvo em situações excepcionalíssimas de grave dano.",
        "fundamentacao_legal": {
            "EOAB": "Art. 7º, XIX",
            "CED": "Art. 34"
        },
        "tags": ["sigilo profissional", "ética", "deveres do advogado"],
        "eh_trap": False
    }
]

def adicionar_questoes():
    """Adiciona questões ao banco de dados"""
    from database.connection import DatabaseManager

    db_manager = DatabaseManager()
    Session = db_manager.get_scoped_session()
    db = Session()

    questoes_adicionadas = 0
    questoes_duplicadas = 0

    print("🚀 Iniciando adição de questões OAB...\n")

    try:
        for q in QUESTOES:
            try:
                questao = QuestaoBanco(**q)
                db.add(questao)
                db.commit()
                questoes_adicionadas += 1
                print(f"✅ [{q['codigo_questao']}] {q['disciplina']} - {q['topico']}")
            except IntegrityError:
                db.rollback()
                questoes_duplicadas += 1
                print(f"⚠️  [{q['codigo_questao']}] Já existe no banco")
            except Exception as e:
                db.rollback()
                print(f"❌ [{q['codigo_questao']}] Erro: {str(e)}")
    finally:
        db.close()

    print(f"\n📊 Resumo:")
    print(f"   ✅ Questões adicionadas: {questoes_adicionadas}")
    print(f"   ⚠️  Questões duplicadas: {questoes_duplicadas}")
    print(f"   📚 Total no banco: {questoes_adicionadas + questoes_duplicadas}")
    print(f"\n🎉 Processo concluído!")

if __name__ == "__main__":
    adicionar_questoes()
