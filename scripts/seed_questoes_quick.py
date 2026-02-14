"""
Seed rapido de 20 questoes para teste
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DATABASE_URL", "postgresql://juris_ia_user:changeme123@localhost:54320/juris_ia")

from database.connection import DatabaseManager
from database.models import QuestaoBanco, DificuldadeQuestao

db_manager = DatabaseManager()
Session = db_manager.get_session_factory()
db = Session()

questoes = [
    {"codigo_questao": "SEED_001", "disciplina": "Direito Penal", "topico": "Parte Geral", "enunciado": "Qual o principio que impede a retroatividade da lei penal mais gravosa?", "alternativas": {"A": "Principio da legalidade", "B": "Principio da anterioridade", "C": "Principio da irretroatividade da lei mais gravosa", "D": "Principio da reserva legal"}, "alternativa_correta": "C", "dificuldade": DificuldadeQuestao.MEDIO, "ativa": True},
    {"codigo_questao": "SEED_002", "disciplina": "Direito Penal", "topico": "Parte Geral", "enunciado": "O que caracteriza o dolo eventual?", "alternativas": {"A": "O agente quer o resultado", "B": "O agente assume o risco de produzir o resultado", "C": "O agente age com negligencia", "D": "O agente age com imprudencia"}, "alternativa_correta": "B", "dificuldade": DificuldadeQuestao.MEDIO, "ativa": True},
    {"codigo_questao": "SEED_003", "disciplina": "Direito Penal", "topico": "Parte Especial", "enunciado": "Qual a pena base do crime de homicidio simples (art. 121 CP)?", "alternativas": {"A": "1 a 4 anos", "B": "6 a 20 anos", "C": "12 a 30 anos", "D": "2 a 8 anos"}, "alternativa_correta": "B", "dificuldade": DificuldadeQuestao.FACIL, "ativa": True},
    {"codigo_questao": "SEED_004", "disciplina": "Direito Penal", "topico": "Parte Geral", "enunciado": "A legitima defesa exige que a agressao seja:", "alternativas": {"A": "Futura e certa", "B": "Passada e consumada", "C": "Injusta, atual ou iminente", "D": "Apenas atual"}, "alternativa_correta": "C", "dificuldade": DificuldadeQuestao.MEDIO, "ativa": True},
    {"codigo_questao": "SEED_005", "disciplina": "Direito Penal", "topico": "Parte Geral", "enunciado": "O que e crime impossivel?", "alternativas": {"A": "Crime sem vitima", "B": "Crime sem pena", "C": "Quando por ineficacia absoluta do meio ou impropriedade absoluta do objeto e impossivel consumar", "D": "Crime prescrito"}, "alternativa_correta": "C", "dificuldade": DificuldadeQuestao.DIFICIL, "ativa": True},
    {"codigo_questao": "SEED_006", "disciplina": "Direito Civil", "topico": "Parte Geral", "enunciado": "A capacidade civil plena se adquire aos:", "alternativas": {"A": "16 anos", "B": "18 anos", "C": "21 anos", "D": "14 anos"}, "alternativa_correta": "B", "dificuldade": DificuldadeQuestao.FACIL, "ativa": True},
    {"codigo_questao": "SEED_007", "disciplina": "Direito Civil", "topico": "Obrigacoes", "enunciado": "Na obrigacao solidaria, o credor pode exigir:", "alternativas": {"A": "Apenas parte de cada devedor", "B": "A totalidade de qualquer devedor", "C": "Apenas do devedor principal", "D": "Proporcionalmente a cada devedor"}, "alternativa_correta": "B", "dificuldade": DificuldadeQuestao.MEDIO, "ativa": True},
    {"codigo_questao": "SEED_008", "disciplina": "Direito Civil", "topico": "Contratos", "enunciado": "O contrato de compra e venda se aperfeiçoa com:", "alternativas": {"A": "A entrega da coisa", "B": "O pagamento do preco", "C": "O acordo sobre coisa e preco", "D": "O registro em cartorio"}, "alternativa_correta": "C", "dificuldade": DificuldadeQuestao.MEDIO, "ativa": True},
    {"codigo_questao": "SEED_009", "disciplina": "Direito Civil", "topico": "Responsabilidade Civil", "enunciado": "A responsabilidade civil objetiva independe de:", "alternativas": {"A": "Dano", "B": "Nexo causal", "C": "Culpa", "D": "Acao"}, "alternativa_correta": "C", "dificuldade": DificuldadeQuestao.FACIL, "ativa": True},
    {"codigo_questao": "SEED_010", "disciplina": "Direito Civil", "topico": "Prescricao", "enunciado": "Qual o prazo prescricional geral do Codigo Civil?", "alternativas": {"A": "3 anos", "B": "5 anos", "C": "10 anos", "D": "20 anos"}, "alternativa_correta": "C", "dificuldade": DificuldadeQuestao.MEDIO, "ativa": True},
    {"codigo_questao": "SEED_011", "disciplina": "Direito Constitucional", "topico": "Principios Fundamentais", "enunciado": "Sao fundamentos da Republica Federativa do Brasil, EXCETO:", "alternativas": {"A": "Soberania", "B": "Cidadania", "C": "Pluralismo politico", "D": "Intervencao estatal minima"}, "alternativa_correta": "D", "dificuldade": DificuldadeQuestao.MEDIO, "ativa": True},
    {"codigo_questao": "SEED_012", "disciplina": "Direito Constitucional", "topico": "Direitos Fundamentais", "enunciado": "O habeas corpus protege:", "alternativas": {"A": "O direito de informacao", "B": "A liberdade de locomocao", "C": "O direito de propriedade", "D": "A liberdade de expressao"}, "alternativa_correta": "B", "dificuldade": DificuldadeQuestao.FACIL, "ativa": True},
    {"codigo_questao": "SEED_013", "disciplina": "Direito Constitucional", "topico": "Organizacao do Estado", "enunciado": "Qual ente federativo nao tem poder judiciario proprio?", "alternativas": {"A": "Uniao", "B": "Estados", "C": "Municipios", "D": "Distrito Federal"}, "alternativa_correta": "C", "dificuldade": DificuldadeQuestao.MEDIO, "ativa": True},
    {"codigo_questao": "SEED_014", "disciplina": "Direito Constitucional", "topico": "Controle de Constitucionalidade", "enunciado": "A ADI e julgada pelo:", "alternativas": {"A": "STJ", "B": "STF", "C": "TSE", "D": "TJ estadual"}, "alternativa_correta": "B", "dificuldade": DificuldadeQuestao.FACIL, "ativa": True},
    {"codigo_questao": "SEED_015", "disciplina": "Direito Constitucional", "topico": "Poder Legislativo", "enunciado": "Emenda constitucional requer aprovacao de:", "alternativas": {"A": "Maioria simples em 1 turno", "B": "Maioria absoluta em 2 turnos", "C": "3/5 em 2 turnos nas duas casas", "D": "2/3 em turno unico"}, "alternativa_correta": "C", "dificuldade": DificuldadeQuestao.DIFICIL, "ativa": True},
    {"codigo_questao": "SEED_016", "disciplina": "Etica Profissional", "topico": "Deveres do Advogado", "enunciado": "E dever do advogado perante o cliente:", "alternativas": {"A": "Garantir resultado favoravel", "B": "Informar sobre o andamento do processo", "C": "Aceitar toda causa proposta", "D": "Trabalhar gratuitamente se necessario"}, "alternativa_correta": "B", "dificuldade": DificuldadeQuestao.FACIL, "ativa": True},
    {"codigo_questao": "SEED_017", "disciplina": "Etica Profissional", "topico": "Incompatibilidades", "enunciado": "A advocacia e incompativel com:", "alternativas": {"A": "Magistratura", "B": "Magisterio", "C": "Atividade empresarial", "D": "Mandato legislativo"}, "alternativa_correta": "A", "dificuldade": DificuldadeQuestao.MEDIO, "ativa": True},
    {"codigo_questao": "SEED_018", "disciplina": "Etica Profissional", "topico": "Honorarios", "enunciado": "Os honorarios ad exitum sao:", "alternativas": {"A": "Pagos antecipadamente", "B": "Pagos mensalmente", "C": "Condicionados ao exito da causa", "D": "Fixados pelo juiz"}, "alternativa_correta": "C", "dificuldade": DificuldadeQuestao.MEDIO, "ativa": True},
    {"codigo_questao": "SEED_019", "disciplina": "Etica Profissional", "topico": "Sigilo Profissional", "enunciado": "O sigilo profissional do advogado:", "alternativas": {"A": "Pode ser quebrado a qualquer momento", "B": "E absoluto e permanente", "C": "Termina com o fim do mandato", "D": "So vale em processos judiciais"}, "alternativa_correta": "B", "dificuldade": DificuldadeQuestao.MEDIO, "ativa": True},
    {"codigo_questao": "SEED_020", "disciplina": "Etica Profissional", "topico": "Publicidade", "enunciado": "A publicidade do advogado deve ser:", "alternativas": {"A": "Agressiva e chamativa", "B": "Informativa, discreta e moderada", "C": "Proibida totalmente", "D": "Ilimitada nas redes sociais"}, "alternativa_correta": "B", "dificuldade": DificuldadeQuestao.FACIL, "ativa": True},
]

added = 0
for q in questoes:
    existing = db.query(QuestaoBanco).filter(QuestaoBanco.codigo_questao == q["codigo_questao"]).first()
    if not existing:
        db.add(QuestaoBanco(**q))
        added += 1

db.commit()
total = db.query(QuestaoBanco).filter(QuestaoBanco.ativa == True).count()
print(f"Questoes adicionadas: {added}")
print(f"Total questoes ativas no banco: {total}")
db.close()
