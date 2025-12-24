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
