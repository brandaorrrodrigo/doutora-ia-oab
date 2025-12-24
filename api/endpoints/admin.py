"""
Endpoints administrativos para gerenciar conteúdo
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.connection import get_db_session
from database.models import QuestaoBanco, DificuldadeQuestao

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/create-tables")
async def create_database_tables():
    """
    Cria todas as tabelas do banco de dados
    """
    from database.connection import DatabaseManager

    try:
        db_manager = DatabaseManager()
        db_manager.create_all_tables()

        return {
            "success": True,
            "message": "Todas as tabelas foram criadas com sucesso!",
            "tables_created": True
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao criar tabelas: {str(e)}",
            "error": str(e)
        }

@router.get("/debug-db")
async def debug_database_config():
    """
    Endpoint de debug para verificar configuração do banco
    """
    import os
    from database.connection import DatabaseManager

    db_manager = DatabaseManager()

    return {
        "database_url_exists": bool(os.getenv("DATABASE_URL")),
        "database_url_preview": os.getenv("DATABASE_URL", "NOT_SET")[:50] + "..." if os.getenv("DATABASE_URL") else "NOT_SET",
        "postgres_host": os.getenv("POSTGRES_HOST", "NOT_SET"),
        "postgres_db": os.getenv("POSTGRES_DB", "NOT_SET"),
        "postgres_user": os.getenv("POSTGRES_USER", "NOT_SET"),
        "config_host": db_manager.config.host,
        "config_database": db_manager.config.database,
        "all_env_vars_count": len(os.environ),
        "database_related_vars": {k: v[:50] + "..." if len(v) > 50 else v
                                  for k, v in os.environ.items()
                                  if "DATABASE" in k or "POSTGRES" in k}
    }

# Questões OAB para seed inicial
QUESTOES_SEED = [
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
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "O artigo 7º, XXI, da Constituição Federal garante aviso prévio proporcional ao tempo de serviço, sendo no mínimo de 30 dias.",
        "fundamentacao_legal": {"CF88": "Art. 7º, XXI", "Lei": "Lei 12.506/2011"},
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
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "A legítima defesa está prevista no art. 25 do Código Penal.",
        "fundamentacao_legal": {"CP": "Art. 25"},
        "tags": ["legítima defesa", "excludente de ilicitude"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_03",
        "disciplina": "Direito Civil",
        "topico": "Contratos",
        "subtopico": "Vícios Redibitórios",
        "enunciado": "Pedro comprou um carro usado e, após 20 dias, descobriu que o motor apresentava defeito oculto grave. Sobre os direitos de Pedro, assinale a alternativa CORRETA.",
        "alternativas": {
            "A": "Pedro perdeu o direito de reclamar, pois o prazo é de 15 dias.",
            "B": "Pedro pode exigir abatimento do preço ou redibir o contrato no prazo de 30 dias da descoberta.",
            "C": "Pedro não tem direito algum, pois comprou usado.",
            "D": "Pedro só poderia reclamar se o defeito aparecesse em até 7 dias.",
            "E": "Pedro deve acionar o fabricante do veículo."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Os vícios redibitórios estão nos arts. 441 a 446 do CC. Prazo de 30 dias para móveis.",
        "fundamentacao_legal": {"CC": "Arts. 441 a 446"},
        "tags": ["vícios redibitórios", "contratos"],
        "eh_trap": True,
        "tipo_trap": "Confusão de prazos"
    },
    # DIREITO PROCESSUAL CIVIL
    {
        "codigo_questao": "OAB_XXXVIII_07",
        "disciplina": "Direito Processual Civil",
        "topico": "Recursos",
        "subtopico": "Apelação",
        "enunciado": "Uma sentença que julgou procedente ação de cobrança foi publicada no dia 10/03/2025 (segunda-feira). Considerando que não há litisconsortes com procuradores diferentes, qual o último dia para interposição de apelação?",
        "alternativas": {
            "A": "24/03/2025",
            "B": "25/03/2025",
            "C": "26/03/2025",
            "D": "27/03/2025"
        },
        "alternativa_correta": "D",
        "dificuldade": "DIFICIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "O prazo para apelar é de 15 dias úteis (art. 1.003, §5º, CPC). Contando a partir de 11/03, o 15º dia útil é 27/03/2025.",
        "fundamentacao_legal": {"CPC": "Art. 1.003, §5º"},
        "tags": ["apelação", "prazos processuais", "recursos"],
        "eh_trap": True,
        "tipo_trap": "Contagem de prazo"
    },
    {
        "codigo_questao": "OAB_XXXVIII_08",
        "disciplina": "Direito Processual Civil",
        "topico": "Competência",
        "subtopico": "Foro",
        "enunciado": "Em ação de reparação de danos causados por acidente de trânsito, o foro competente é:",
        "alternativas": {
            "A": "O do domicílio do réu ou o do local do fato.",
            "B": "Exclusivamente o do local do fato.",
            "C": "Exclusivamente o do domicílio do réu.",
            "D": "O do domicílio do autor."
        },
        "alternativa_correta": "A",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 53, IV, CPC: é competente o foro do domicílio do réu ou do local do fato para ação de reparação de dano.",
        "fundamentacao_legal": {"CPC": "Art. 53, IV"},
        "tags": ["competência", "foro", "responsabilidade civil"],
        "eh_trap": False
    },
    # DIREITO TRIBUTÁRIO
    {
        "codigo_questao": "OAB_XXXVIII_09",
        "disciplina": "Direito Tributário",
        "topico": "Impostos",
        "subtopico": "ICMS",
        "enunciado": "Sobre o ICMS, assinale a alternativa INCORRETA:",
        "alternativas": {
            "A": "É um imposto de competência dos Estados e do Distrito Federal.",
            "B": "Incide sobre operações relativas à circulação de mercadorias.",
            "C": "Pode ser progressivo em razão do valor da operação.",
            "D": "É um imposto não-cumulativo."
        },
        "alternativa_correta": "C",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "O ICMS NÃO pode ser progressivo. Pode ser seletivo em função da essencialidade das mercadorias.",
        "fundamentacao_legal": {"CF88": "Art. 155, §2º"},
        "tags": ["ICMS", "impostos estaduais", "não-cumulatividade"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_10",
        "disciplina": "Direito Tributário",
        "topico": "Princípios",
        "subtopico": "Legalidade",
        "enunciado": "De acordo com o princípio da legalidade tributária:",
        "alternativas": {
            "A": "Apenas lei complementar pode instituir tributos.",
            "B": "É vedado exigir ou aumentar tributo sem lei que o estabeleça.",
            "C": "A majoração de tributos depende de aprovação popular.",
            "D": "Os tributos só podem ser cobrados após 90 dias da publicação da lei."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 150, I, CF: é vedado exigir ou aumentar tributo sem lei que o estabeleça.",
        "fundamentacao_legal": {"CF88": "Art. 150, I"},
        "tags": ["princípios tributários", "legalidade"],
        "eh_trap": False
    },
    # ÉTICA PROFISSIONAL
    {
        "codigo_questao": "OAB_XXXVIII_11",
        "disciplina": "Ética Profissional",
        "topico": "Deveres do Advogado",
        "subtopico": "Sigilo Profissional",
        "enunciado": "O sigilo profissional do advogado:",
        "alternativas": {
            "A": "Pode ser quebrado mediante determinação judicial.",
            "B": "É absoluto e não pode ser revelado em hipótese alguma.",
            "C": "Só se aplica a informações obtidas em processos judiciais.",
            "D": "Deve ser revelado se o crime for considerado hediondo."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "O sigilo profissional do advogado é absoluto (art. 7º, XIX, EOAB e art. 34 do Código de Ética).",
        "fundamentacao_legal": {"EOAB": "Art. 7º, XIX", "CED": "Art. 34"},
        "tags": ["sigilo profissional", "ética", "deveres"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_12",
        "disciplina": "Ética Profissional",
        "topico": "Incompatibilidades",
        "subtopico": "Exercício da Advocacia",
        "enunciado": "É incompatível com a advocacia o exercício de:",
        "alternativas": {
            "A": "Cargo de direção em empresa privada.",
            "B": "Magistério jurídico.",
            "C": "Membro do Poder Legislativo Federal.",
            "D": "Consultor jurídico de empresa."
        },
        "alternativa_correta": "C",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 28, III, EOAB: é incompatível com a advocacia o exercício de cargos ou funções vinculados ao Poder Executivo e Judiciário, mas parlamentares podem advogar.",
        "fundamentacao_legal": {"EOAB": "Art. 28"},
        "tags": ["incompatibilidades", "ética", "exercício profissional"],
        "eh_trap": True,
        "tipo_trap": "Parlamentar pode advogar"
    },
    # DIREITO EMPRESARIAL
    {
        "codigo_questao": "OAB_XXXVIII_13",
        "disciplina": "Direito Empresarial",
        "topico": "Sociedades",
        "subtopico": "Tipos Societários",
        "enunciado": "Na sociedade limitada, a responsabilidade de cada sócio:",
        "alternativas": {
            "A": "É ilimitada e solidária.",
            "B": "É restrita ao valor de suas quotas, mas todos respondem solidariamente pela integralização do capital social.",
            "C": "É proporcional à sua participação no capital.",
            "D": "É limitada ao dobro do valor de suas quotas."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 1.052, CC: a responsabilidade de cada sócio é restrita ao valor de suas quotas, mas todos respondem solidariamente pela integralização do capital social.",
        "fundamentacao_legal": {"CC": "Art. 1.052"},
        "tags": ["sociedade limitada", "responsabilidade", "capital social"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_14",
        "disciplina": "Direito Empresarial",
        "topico": "Títulos de Crédito",
        "subtopico": "Cheque",
        "enunciado": "O prazo de apresentação do cheque ao banco sacado é:",
        "alternativas": {
            "A": "30 dias da emissão, se da mesma praça; 60 dias, se de praças diferentes.",
            "B": "15 dias da emissão.",
            "C": "90 dias da emissão.",
            "D": "6 meses da emissão."
        },
        "alternativa_correta": "A",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Lei do Cheque, art. 33: prazo de 30 dias (mesma praça) ou 60 dias (praças diferentes).",
        "fundamentacao_legal": {"Lei": "Lei 7.357/85, art. 33"},
        "tags": ["cheque", "títulos de crédito", "prazos"],
        "eh_trap": False
    },
    # DIREITO DO TRABALHO
    {
        "codigo_questao": "OAB_XXXVIII_15",
        "disciplina": "Direito do Trabalho",
        "topico": "Rescisão",
        "subtopico": "Verbas Rescisórias",
        "enunciado": "Em caso de demissão sem justa causa, o empregado NÃO tem direito a:",
        "alternativas": {
            "A": "Aviso prévio indenizado.",
            "B": "Saldo de salário.",
            "C": "Férias proporcionais.",
            "D": "Seguro-desemprego em qualquer hipótese."
        },
        "alternativa_correta": "D",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "O seguro-desemprego depende de requisitos específicos (tempo de trabalho, etc), não é automático.",
        "fundamentacao_legal": {"Lei": "Lei 7.998/90"},
        "tags": ["rescisão", "verbas rescisórias", "seguro-desemprego"],
        "eh_trap": False
    },
    # DIREITO PROCESSUAL PENAL
    {
        "codigo_questao": "OAB_XXXVIII_16",
        "disciplina": "Direito Processual Penal",
        "topico": "Prisões",
        "subtopico": "Prisão em Flagrante",
        "enunciado": "A prisão em flagrante é obrigatória quando:",
        "alternativas": {
            "A": "Qualquer pessoa estiver cometendo crime.",
            "B": "Houver mandado judicial.",
            "C": "A autoridade policial tiver fundadas suspeitas.",
            "D": "O crime for inafiançável."
        },
        "alternativa_correta": "A",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 301, CPP: Qualquer do povo poderá e as autoridades policiais e seus agentes deverão prender quem quer que seja encontrado em flagrante delito.",
        "fundamentacao_legal": {"CPP": "Art. 301"},
        "tags": ["prisão em flagrante", "processo penal"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_17",
        "disciplina": "Direito Processual Penal",
        "topico": "Ação Penal",
        "subtopico": "Titularidade",
        "enunciado": "A ação penal pública é de titularidade:",
        "alternativas": {
            "A": "Do ofendido ou seu representante legal.",
            "B": "Do Ministério Público.",
            "C": "Do juiz de direito.",
            "D": "Da autoridade policial."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "CF/88, art. 129, I: é função institucional do MP promover privativamente a ação penal pública.",
        "fundamentacao_legal": {"CF88": "Art. 129, I"},
        "tags": ["ação penal", "ministério público"],
        "eh_trap": False
    },
    # DIREITO CONSTITUCIONAL
    {
        "codigo_questao": "OAB_XXXVIII_18",
        "disciplina": "Direito Constitucional",
        "topico": "Controle de Constitucionalidade",
        "subtopico": "ADI",
        "enunciado": "Podem propor Ação Direta de Inconstitucionalidade (ADI):",
        "alternativas": {
            "A": "Qualquer cidadão no pleno gozo dos direitos políticos.",
            "B": "Apenas o Presidente da República e o Procurador-Geral da República.",
            "C": "Os legitimados do art. 103 da CF/88.",
            "D": "Exclusivamente o Supremo Tribunal Federal."
        },
        "alternativa_correta": "C",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 103, CF: lista os legitimados para propor ADI (Presidente, Mesa do Senado/Câmara, Governador, PGR, Conselho Federal da OAB, etc).",
        "fundamentacao_legal": {"CF88": "Art. 103"},
        "tags": ["controle de constitucionalidade", "ADI"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_19",
        "disciplina": "Direito Constitucional",
        "topico": "Organização do Estado",
        "subtopico": "Competências",
        "enunciado": "É competência privativa da União legislar sobre:",
        "alternativas": {
            "A": "Educação e cultura.",
            "B": "Direito civil, comercial, penal e processual.",
            "C": "Proteção ao meio ambiente.",
            "D": "Orçamento municipal."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 22, I, CF: compete privativamente à União legislar sobre direito civil, comercial, penal, processual, etc.",
        "fundamentacao_legal": {"CF88": "Art. 22, I"},
        "tags": ["competências legislativas", "federalismo"],
        "eh_trap": False
    },
    # DIREITO CIVIL
    {
        "codigo_questao": "OAB_XXXVIII_20",
        "disciplina": "Direito Civil",
        "topico": "Responsabilidade Civil",
        "subtopico": "Dano Moral",
        "enunciado": "Para a configuração do dano moral, é necessário:",
        "alternativas": {
            "A": "Prova do prejuízo material.",
            "B": "Demonstração de dor física.",
            "C": "Violação de direito da personalidade.",
            "D": "Culpa grave ou dolo do agente."
        },
        "alternativa_correta": "C",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Dano moral decorre da violação de direitos da personalidade (honra, imagem, intimidade, etc).",
        "fundamentacao_legal": {"CC": "Arts. 186 e 927"},
        "tags": ["dano moral", "responsabilidade civil"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_21",
        "disciplina": "Direito Civil",
        "topico": "Casamento",
        "subtopico": "Regime de Bens",
        "enunciado": "No regime da comunhão parcial de bens:",
        "alternativas": {
            "A": "Todos os bens, anteriores e posteriores ao casamento, são comunicáveis.",
            "B": "Apenas os bens adquiridos onerosamente na constância do casamento são comuns.",
            "C": "Nenhum bem se comunica.",
            "D": "Apenas os bens móveis se comunicam."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 1.658, CC: Na comunhão parcial, comunicam-se os bens adquiridos onerosamente na constância do casamento.",
        "fundamentacao_legal": {"CC": "Art. 1.658"},
        "tags": ["casamento", "regime de bens"],
        "eh_trap": False
    },
    # DIREITO PENAL
    {
        "codigo_questao": "OAB_XXXVIII_22",
        "disciplina": "Direito Penal",
        "topico": "Penas",
        "subtopico": "Prescrição",
        "enunciado": "A prescrição da pretensão punitiva regula-se:",
        "alternativas": {
            "A": "Pela pena em abstrato prevista no tipo penal.",
            "B": "Pela pena efetivamente aplicada na sentença.",
            "C": "Sempre pelo prazo de 20 anos.",
            "D": "Pela gravidade do crime cometido."
        },
        "alternativa_correta": "A",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 109, CP: A prescrição antes de transitar em julgado regula-se pelo máximo da pena privativa de liberdade cominada ao crime.",
        "fundamentacao_legal": {"CP": "Art. 109"},
        "tags": ["prescrição", "pretensão punitiva"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_23",
        "disciplina": "Direito Penal",
        "topico": "Crimes Contra o Patrimônio",
        "subtopico": "Furto",
        "enunciado": "O furto qualificado pelo rompimento de obstáculo caracteriza-se quando:",
        "alternativas": {
            "A": "A vítima estava dormindo.",
            "B": "Há destruição ou rompimento de obstáculo à subtração da coisa.",
            "C": "O crime é cometido durante o repouso noturno.",
            "D": "Participam duas ou mais pessoas."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 155, §4º, I, CP: qualifica-se o furto quando há destruição ou rompimento de obstáculo.",
        "fundamentacao_legal": {"CP": "Art. 155, §4º, I"},
        "tags": ["furto qualificado", "crimes contra o patrimônio"],
        "eh_trap": False
    },
    # DIREITOS HUMANOS
    {
        "codigo_questao": "OAB_XXXVIII_24",
        "disciplina": "Direitos Humanos",
        "topico": "Sistema Interamericano",
        "subtopico": "Corte IDH",
        "enunciado": "A Corte Interamericana de Direitos Humanos tem jurisdição:",
        "alternativas": {
            "A": "Automática sobre todos os países da América.",
            "B": "Apenas consultiva, sem poder de condenação.",
            "C": "Contenciosa e consultiva, mas depende de aceitação expressa do Estado.",
            "D": "Exclusivamente sobre casos de genocídio."
        },
        "alternativa_correta": "C",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "A jurisdição contenciosa da Corte IDH depende de declaração de aceitação do Estado (art. 62, Convenção Americana).",
        "fundamentacao_legal": {"CADH": "Art. 62"},
        "tags": ["direitos humanos", "corte IDH"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_25",
        "disciplina": "Direitos Humanos",
        "topico": "Tratados Internacionais",
        "subtopico": "Incorporação",
        "enunciado": "Tratados de direitos humanos aprovados com quórum de emenda constitucional:",
        "alternativas": {
            "A": "Têm status supralegal.",
            "B": "Têm equivalência a emendas constitucionais.",
            "C": "São inconstitucionais.",
            "D": "Têm status de lei ordinária."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 5º, §3º, CF: tratados de direitos humanos aprovados por 3/5 em dois turnos equivalem a emendas constitucionais.",
        "fundamentacao_legal": {"CF88": "Art. 5º, §3º"},
        "tags": ["tratados", "direitos humanos", "hierarquia"],
        "eh_trap": False
    },
    # MAIS DIREITO DO TRABALHO
    {
        "codigo_questao": "OAB_XXXVIII_26",
        "disciplina": "Direito do Trabalho",
        "topico": "Jornada",
        "subtopico": "Horas Extras",
        "enunciado": "O adicional de horas extras deve ser, no mínimo:",
        "alternativas": {
            "A": "30% sobre o valor da hora normal.",
            "B": "50% sobre o valor da hora normal.",
            "C": "100% sobre o valor da hora normal.",
            "D": "25% sobre o valor da hora normal."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 7º, XVI, CF: remuneração do serviço extraordinário superior, no mínimo, em 50% à do normal.",
        "fundamentacao_legal": {"CF88": "Art. 7º, XVI"},
        "tags": ["horas extras", "jornada de trabalho"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_27",
        "disciplina": "Direito do Trabalho",
        "topico": "Férias",
        "subtopico": "Período Aquisitivo",
        "enunciado": "O empregado perde o direito às férias quando:",
        "alternativas": {
            "A": "Deixar o emprego e não for readmitido em 60 dias.",
            "B": "Permanecer em licença remunerada por mais de 30 dias.",
            "C": "Faltar injustificadamente por mais de 5 dias no período aquisitivo.",
            "D": "Receber auxílio-doença por mais de 6 meses."
        },
        "alternativa_correta": "D",
        "dificuldade": "DIFICIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 133, IV, CLT: perde o direito a férias quem permanecer em gozo de auxílio-doença por mais de 6 meses, mesmo descontínuos.",
        "fundamentacao_legal": {"CLT": "Art. 133, IV"},
        "tags": ["férias", "perda do direito"],
        "eh_trap": True,
        "tipo_trap": "Prazo - 6 meses vs outros prazos"
    },
    # MAIS ÉTICA
    {
        "codigo_questao": "OAB_XXXVIII_28",
        "disciplina": "Ética Profissional",
        "topico": "Honorários",
        "subtopico": "Contrato",
        "enunciado": "O contrato de honorários advocatícios:",
        "alternativas": {
            "A": "Deve sempre ser verbal para facilitar acordos.",
            "B": "Pode ser escrito ou verbal, mas é recomendável a forma escrita.",
            "C": "É obrigatoriamente registrado na OAB.",
            "D": "Só é válido se houver duas testemunhas."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 48, EOAB: O contrato pode ser escrito ou verbal, mas a forma escrita é recomendável para evitar controvérsias.",
        "fundamentacao_legal": {"EOAB": "Art. 48"},
        "tags": ["honorários", "contrato"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_29",
        "disciplina": "Ética Profissional",
        "topico": "Publicidade",
        "subtopico": "Limites",
        "enunciado": "É vedado ao advogado em sua publicidade profissional:",
        "alternativas": {
            "A": "Mencionar suas especializações.",
            "B": "Divulgar preços de serviços.",
            "C": "Referir-se de forma depreciatória a colegas.",
            "D": "Informar endereço do escritório."
        },
        "alternativa_correta": "C",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 31, CED: É vedada a publicidade de qualquer espécie que deprecie outros advogados.",
        "fundamentacao_legal": {"CED": "Art. 31"},
        "tags": ["publicidade", "ética", "vedações"],
        "eh_trap": False
    },
    # MAIS PROCESSUAL CIVIL
    {
        "codigo_questao": "OAB_XXXVIII_30",
        "disciplina": "Direito Processual Civil",
        "topico": "Provas",
        "subtopico": "Ônus da Prova",
        "enunciado": "Sobre o ônus da prova, é correto afirmar:",
        "alternativas": {
            "A": "Cabe sempre ao autor provar todos os fatos.",
            "B": "Ao autor incumbe provar o fato constitutivo do seu direito; ao réu, fato impeditivo, modificativo ou extintivo.",
            "C": "O réu nunca tem ônus probatório.",
            "D": "Apenas o autor tem ônus da prova."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 373, CPC: ao autor incumbe provar fato constitutivo; ao réu, fatos impeditivos, modificativos ou extintivos do direito do autor.",
        "fundamentacao_legal": {"CPC": "Art. 373"},
        "tags": ["ônus da prova", "provas"],
        "eh_trap": False
    },
    # MAIS QUESTÕES PARA COMPLETAR 50+
    {
        "codigo_questao": "OAB_XXXVIII_31",
        "disciplina": "Direito Administrativo",
        "topico": "Licitações",
        "subtopico": "Modalidades",
        "enunciado": "O pregão é modalidade de licitação destinada a:",
        "alternativas": {
            "A": "Obras de grande porte.",
            "B": "Aquisição de bens e serviços comuns.",
            "C": "Alienação de bens imóveis.",
            "D": "Contratação de serviços de engenharia."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Lei 10.520/02: pregão destina-se à aquisição de bens e serviços comuns, independentemente do valor.",
        "fundamentacao_legal": {"Lei": "Lei 10.520/02"},
        "tags": ["licitação", "pregão", "administrativo"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_32",
        "disciplina": "Direito Administrativo",
        "topico": "Atos Administrativos",
        "subtopico": "Atributos",
        "enunciado": "A presunção de legitimidade dos atos administrativos significa que:",
        "alternativas": {
            "A": "O ato é sempre legal e não pode ser questionado.",
            "B": "Presume-se que o ato foi praticado conforme a lei, até prova em contrário.",
            "C": "O ato não pode ser revogado.",
            "D": "Apenas o Poder Judiciário pode questionar o ato."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Presunção de legitimidade é relativa (juris tantum), admitindo prova em contrário.",
        "fundamentacao_legal": {"Doutrina": "Atributos dos atos administrativos"},
        "tags": ["atos administrativos", "presunção de legitimidade"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_33",
        "disciplina": "Direito Ambiental",
        "topico": "Responsabilidade",
        "subtopico": "Dano Ambiental",
        "enunciado": "A responsabilidade por dano ambiental é:",
        "alternativas": {
            "A": "Subjetiva, exigindo prova de culpa.",
            "B": "Objetiva, independentemente de culpa.",
            "C": "Exclusiva da pessoa física.",
            "D": "Limitada a danos materiais."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 14, §1º, Lei 6.938/81: responsabilidade objetiva por dano ambiental.",
        "fundamentacao_legal": {"Lei": "Lei 6.938/81, art. 14, §1º"},
        "tags": ["dano ambiental", "responsabilidade objetiva"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_34",
        "disciplina": "Direito do Consumidor",
        "topico": "Relação de Consumo",
        "subtopico": "Conceitos",
        "enunciado": "É considerado consumidor:",
        "alternativas": {
            "A": "Apenas a pessoa física que adquire produto ou serviço.",
            "B": "A pessoa física ou jurídica que adquire ou utiliza produto ou serviço como destinatário final.",
            "C": "Exclusivamente quem compra produtos.",
            "D": "Apenas quem adquire serviços."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 2º, CDC: consumidor é toda pessoa física ou jurídica que adquire ou utiliza produto ou serviço como destinatário final.",
        "fundamentacao_legal": {"CDC": "Art. 2º"},
        "tags": ["consumidor", "destinatário final"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_35",
        "disciplina": "Direito do Consumidor",
        "topico": "Vícios",
        "subtopico": "Prazo",
        "enunciado": "O prazo para reclamar de vícios aparentes em produtos duráveis é de:",
        "alternativas": {
            "A": "30 dias.",
            "B": "90 dias.",
            "C": "1 ano.",
            "D": "5 anos."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 26, II, CDC: prazo de 90 dias para reclamar de vícios aparentes em produtos duráveis.",
        "fundamentacao_legal": {"CDC": "Art. 26, II"},
        "tags": ["vícios", "prazo", "produto durável"],
        "eh_trap": True,
        "tipo_trap": "Prazo - 30 vs 90 dias"
    },
    {
        "codigo_questao": "OAB_XXXVIII_36",
        "disciplina": "Direito Penal",
        "topico": "Crimes Contra a Pessoa",
        "subtopico": "Homicídio",
        "enunciado": "O homicídio qualificado pelo motivo torpe ocorre quando:",
        "alternativas": {
            "A": "O crime é cometido mediante paga.",
            "B": "O crime é praticado por motivo repugnante, abjeto.",
            "C": "O crime é praticado com emprego de veneno.",
            "D": "O crime é cometido à traição."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 121, §2º, I, CP: motivo torpe é o repugnante, abjeto, vil.",
        "fundamentacao_legal": {"CP": "Art. 121, §2º, I"},
        "tags": ["homicídio qualificado", "motivo torpe"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_37",
        "disciplina": "Direito Constitucional",
        "topico": "Poder Legislativo",
        "subtopico": "Imunidades",
        "enunciado": "A imunidade parlamentar material significa que:",
        "alternativas": {
            "A": "Deputados e Senadores não podem ser presos.",
            "B": "Parlamentares são invioláveis por suas opiniões, palavras e votos.",
            "C": "Parlamentares não podem ser processados.",
            "D": "Parlamentares têm foro privilegiado."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 53, CF: imunidade material garante inviolabilidade por opiniões, palavras e votos.",
        "fundamentacao_legal": {"CF88": "Art. 53"},
        "tags": ["imunidade parlamentar", "inviolabilidade"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_38",
        "disciplina": "Direito Civil",
        "topico": "Sucessões",
        "subtopico": "Testamento",
        "enunciado": "O testamento público:",
        "alternativas": {
            "A": "É escrito pelo próprio testador.",
            "B": "É lavrado por tabelião ou substituto legal.",
            "C": "Não precisa de testemunhas.",
            "D": "É sempre revogável por escritura pública."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 1.864, CC: testamento público é escrito por tabelião em seu livro de notas.",
        "fundamentacao_legal": {"CC": "Art. 1.864"},
        "tags": ["testamento público", "sucessões"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_39",
        "disciplina": "Direito Empresarial",
        "topico": "Falência",
        "subtopico": "Requisitos",
        "enunciado": "Pode requerer falência de empresário:",
        "alternativas": {
            "A": "Apenas o próprio devedor.",
            "B": "O próprio devedor, o cônjuge sobrevivente ou qualquer credor.",
            "C": "Exclusivamente o Ministério Público.",
            "D": "Apenas credores trabalhistas."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 97, Lei 11.101/05: podem requerer falência o próprio devedor, cônjuge sobrevivente, herdeiros, inventariante, sócio ou qualquer credor.",
        "fundamentacao_legal": {"Lei": "Lei 11.101/05, art. 97"},
        "tags": ["falência", "legitimidade"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_40",
        "disciplina": "Direito Processual Civil",
        "topico": "Petição Inicial",
        "subtopico": "Requisitos",
        "enunciado": "São requisitos essenciais da petição inicial:",
        "alternativas": {
            "A": "Apenas a indicação do juiz e o pedido.",
            "B": "Endereço das partes, fatos e fundamentos jurídicos, pedido e valor da causa.",
            "C": "Somente o nome das partes e o pedido.",
            "D": "Apenas os fundamentos jurídicos."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 319, CPC: a petição inicial deve conter, entre outros, endereço das partes, fatos e fundamentos, pedido e valor da causa.",
        "fundamentacao_legal": {"CPC": "Art. 319"},
        "tags": ["petição inicial", "requisitos"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_41",
        "disciplina": "Direito Tributário",
        "topico": "Competência",
        "subtopico": "Impostos Municipais",
        "enunciado": "É imposto de competência dos Municípios:",
        "alternativas": {
            "A": "ICMS.",
            "B": "IPTU.",
            "C": "ITCMD.",
            "D": "IOF."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 156, I, CF: compete aos Municípios instituir imposto sobre propriedade predial e territorial urbana (IPTU).",
        "fundamentacao_legal": {"CF88": "Art. 156, I"},
        "tags": ["IPTU", "competência municipal"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_42",
        "disciplina": "Direito do Trabalho",
        "topico": "FGTS",
        "subtopico": "Multa",
        "enunciado": "Na dispensa sem justa causa, o empregador deve pagar multa de FGTS de:",
        "alternativas": {
            "A": "20% sobre o saldo.",
            "B": "40% sobre o saldo.",
            "C": "50% sobre o saldo.",
            "D": "10% sobre o saldo."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 18, §1º, Lei 8.036/90: multa de 40% sobre o saldo do FGTS na dispensa sem justa causa.",
        "fundamentacao_legal": {"Lei": "Lei 8.036/90, art. 18, §1º"},
        "tags": ["FGTS", "multa", "rescisão"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_43",
        "disciplina": "Ética Profissional",
        "topico": "OAB",
        "subtopico": "Inscrição",
        "enunciado": "Para inscrição nos quadros da OAB, é necessário:",
        "alternativas": {
            "A": "Apenas diploma de bacharel em Direito.",
            "B": "Aprovação no Exame de Ordem e idoneidade moral.",
            "C": "Cinco anos de experiência jurídica.",
            "D": "Recomendação de três advogados."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 8º, EOAB: requisitos incluem capacidade civil, diploma, aprovação no Exame de Ordem e idoneidade moral.",
        "fundamentacao_legal": {"EOAB": "Art. 8º"},
        "tags": ["inscrição OAB", "exame de ordem"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_44",
        "disciplina": "Direito Processual Penal",
        "topico": "Provas",
        "subtopico": "Provas Ilícitas",
        "enunciado": "Provas obtidas por meios ilícitos são:",
        "alternativas": {
            "A": "Válidas se essenciais à condenação.",
            "B": "Inadmissíveis no processo.",
            "C": "Válidas apenas na defesa.",
            "D": "Admitidas com ressalvas."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 5º, LVI, CF e art. 157, CPP: são inadmissíveis as provas obtidas por meios ilícitos.",
        "fundamentacao_legal": {"CF88": "Art. 5º, LVI", "CPP": "Art. 157"},
        "tags": ["provas ilícitas", "inadmissibilidade"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_45",
        "disciplina": "Direito Civil",
        "topico": "Obrigações",
        "subtopico": "Mora",
        "enunciado": "Na obrigação positiva e líquida, o devedor considera-se em mora:",
        "alternativas": {
            "A": "Apenas após interpelação judicial.",
            "B": "Desde o vencimento.",
            "C": "Após 30 dias do vencimento.",
            "D": "Quando for notificado extrajudicialmente."
        },
        "alternativa_correta": "B",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 397, CC: o devedor em mora desde o vencimento quando a obrigação for positiva, líquida e com termo.",
        "fundamentacao_legal": {"CC": "Art. 397"},
        "tags": ["mora", "obrigações", "vencimento"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_46",
        "disciplina": "Direito Penal",
        "topico": "Concurso de Crimes",
        "subtopico": "Concurso Formal",
        "enunciado": "No concurso formal de crimes:",
        "alternativas": {
            "A": "Aplica-se a pena do crime mais grave aumentada.",
            "B": "Somam-se todas as penas.",
            "C": "Aplica-se apenas a pena do crime mais grave.",
            "D": "Não há aumento de pena."
        },
        "alternativa_correta": "A",
        "dificuldade": "MEDIO",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 70, CP: concurso formal - aplica-se a mais grave das penas cabíveis ou, se iguais, uma delas, aumentada de 1/6 a 1/2.",
        "fundamentacao_legal": {"CP": "Art. 70"},
        "tags": ["concurso formal", "penas"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_47",
        "disciplina": "Direito Constitucional",
        "topico": "Remédios Constitucionais",
        "subtopico": "Habeas Data",
        "enunciado": "O habeas data destina-se a:",
        "alternativas": {
            "A": "Proteger a liberdade de locomoção.",
            "B": "Conhecer e retificar informações constantes de registros públicos.",
            "C": "Anular ato lesivo ao patrimônio público.",
            "D": "Suspender ato normativo."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 5º, LXXII, CF: habeas data para conhecer informações pessoais em registros e para retificação.",
        "fundamentacao_legal": {"CF88": "Art. 5º, LXXII"},
        "tags": ["habeas data", "remédios constitucionais"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_48",
        "disciplina": "Direito Empresarial",
        "topico": "Nome Empresarial",
        "subtopico": "Espécies",
        "enunciado": "A firma individual é formada por:",
        "alternativas": {
            "A": "Nome fantasia escolhido livremente.",
            "B": "Nome civil do empresário, completo ou abreviado.",
            "C": "Sigla do ramo de atividade.",
            "D": "Nome de terceiros."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 1.156, CC: o empresário individual opera sob firma constituída por seu nome, completo ou abreviado.",
        "fundamentacao_legal": {"CC": "Art. 1.156"},
        "tags": ["nome empresarial", "firma individual"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_49",
        "disciplina": "Direito Administrativo",
        "topico": "Servidores Públicos",
        "subtopico": "Estabilidade",
        "enunciado": "O servidor público adquire estabilidade após:",
        "alternativas": {
            "A": "1 ano de efetivo exercício.",
            "B": "2 anos de efetivo exercício.",
            "C": "3 anos de efetivo exercício.",
            "D": "5 anos de efetivo exercício."
        },
        "alternativa_correta": "C",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 41, CF: o servidor adquire estabilidade após 3 anos de efetivo exercício, mediante avaliação de desempenho.",
        "fundamentacao_legal": {"CF88": "Art. 41"},
        "tags": ["estabilidade", "servidores públicos"],
        "eh_trap": False
    },
    {
        "codigo_questao": "OAB_XXXVIII_50",
        "disciplina": "Direito do Consumidor",
        "topico": "Responsabilidade",
        "subtopico": "Fato do Produto",
        "enunciado": "A responsabilidade pelo fato do produto é:",
        "alternativas": {
            "A": "Subjetiva.",
            "B": "Objetiva.",
            "C": "Solidária apenas entre fabricantes.",
            "D": "Exclusiva do comerciante."
        },
        "alternativa_correta": "B",
        "dificuldade": "FACIL",
        "ano_prova": 2024,
        "numero_exame": "XXXVIII",
        "explicacao_detalhada": "Art. 12, CDC: responsabilidade objetiva do fabricante, produtor, construtor e importador por defeitos do produto.",
        "fundamentacao_legal": {"CDC": "Art. 12"},
        "tags": ["fato do produto", "responsabilidade objetiva"],
        "eh_trap": False
    }
]

@router.post("/seed-questoes")
async def seed_questoes():
    """
    Adiciona questões iniciais ao banco de dados
    Endpoint temporário para popular o sistema
    """
    from database.connection import DatabaseManager

    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    adicionadas = 0
    duplicadas = 0
    erros = []

    try:
        for q_data in QUESTOES_SEED:
            try:
                questao = QuestaoBanco(**q_data)
                db.add(questao)
                db.commit()
                adicionadas += 1
            except IntegrityError:
                db.rollback()
                duplicadas += 1
            except Exception as e:
                db.rollback()
                erros.append({
                    "questao": q_data.get("codigo_questao"),
                    "erro": str(e)
                })
    finally:
        db.close()

    return {
        "success": True,
        "questoes_adicionadas": adicionadas,
        "questoes_duplicadas": duplicadas,
        "total_questoes": len(QUESTOES_SEED),
        "erros": erros if erros else None
    }

@router.get("/stats")
async def get_database_stats():
    """
    Retorna estatísticas do banco de dados
    """
    from database.connection import DatabaseManager
    from sqlalchemy import func

    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        total_questoes = db.query(func.count(QuestaoBanco.id)).scalar()

        questoes_por_disciplina = db.query(
            QuestaoBanco.disciplina,
            func.count(QuestaoBanco.id)
        ).group_by(QuestaoBanco.disciplina).all()

        questoes_por_dificuldade = db.query(
            QuestaoBanco.dificuldade,
            func.count(QuestaoBanco.id)
        ).group_by(QuestaoBanco.dificuldade).all()

        return {
            "success": True,
            "total_questoes": total_questoes,
            "por_disciplina": {disc: count for disc, count in questoes_por_disciplina},
            "por_dificuldade": {dif: count for dif, count in questoes_por_dificuldade}
        }
    finally:
        db.close()
