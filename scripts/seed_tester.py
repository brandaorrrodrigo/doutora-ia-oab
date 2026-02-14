"""
Script Seed para Testers
========================

Cria dados prontos para testar o fluxo completo:
1. Usuario tester: tester@jurisia.com / tester123
2. PerfilJuridico com dados intermediarios
3. 3 sessoes de estudo completas (com interacoes)
4. Progresso em 5 disciplinas

Execucao:
  cd D:\\JURIS_IA_CORE_V1
  python scripts/seed_tester.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from database.connection import DatabaseManager
from database.models import (
    User, PerfilJuridico, SessaoEstudo, InteracaoQuestao,
    ProgressoDisciplina, QuestaoBanco,
    UserStatus, NivelDominio, TipoResposta, DificuldadeQuestao
)

# Credenciais do tester
TESTER_EMAIL = "tester@jurisia.com"
TESTER_SENHA = "tester123"
TESTER_NOME = "Tester JURIS IA"


def hash_tester_password(senha: str) -> str:
    """Hash da senha usando bcrypt (mesmo do api/auth.py)"""
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(senha)
    except ImportError:
        # Fallback para SHA256 (compativel com admin.py)
        import hashlib
        print("  AVISO: passlib nao instalado, usando SHA256 (compativel com /admin/login)")
        return hashlib.sha256(senha.encode()).hexdigest()


def seed():
    print("=" * 70)
    print("SEED TESTER - Criando dados para teste")
    print("=" * 70)

    db_manager = DatabaseManager()
    SessionFactory = db_manager.get_session_factory()
    db = SessionFactory()

    try:
        # ================================================================
        # 1. CRIAR USUARIO TESTER
        # ================================================================
        print("\n[1/5] Criando usuario tester...")

        existing = db.query(User).filter(User.email == TESTER_EMAIL).first()
        if existing:
            print(f"  Usuario ja existe (id={existing.id}). Usando existente.")
            tester = existing
        else:
            password_hash = hash_tester_password(TESTER_SENHA)
            tester = User(
                nome=TESTER_NOME,
                email=TESTER_EMAIL,
                password_hash=password_hash,
                status=UserStatus.ATIVO,
                ultimo_acesso=datetime.utcnow()
            )
            db.add(tester)
            db.flush()
            print(f"  Criado: {tester.nome} ({tester.email}) id={tester.id}")

        # ================================================================
        # 2. CRIAR PERFIL JURIDICO
        # ================================================================
        print("\n[2/5] Criando perfil juridico...")

        perfil = db.query(PerfilJuridico).filter(
            PerfilJuridico.user_id == tester.id
        ).first()

        if perfil:
            print(f"  Perfil ja existe. Atualizando dados...")
            perfil.nivel_geral = NivelDominio.INTERMEDIARIO
            perfil.pontuacao_global = 350
            perfil.taxa_acerto_global = 68.5
            perfil.total_questoes_respondidas = 45
            perfil.total_questoes_corretas = 31
            perfil.total_tempo_estudo_minutos = 120
            perfil.sequencia_dias_consecutivos = 3
        else:
            perfil = PerfilJuridico(
                user_id=tester.id,
                nivel_geral=NivelDominio.INTERMEDIARIO,
                pontuacao_global=350,
                taxa_acerto_global=68.5,
                total_questoes_respondidas=45,
                total_questoes_corretas=31,
                total_tempo_estudo_minutos=120,
                sequencia_dias_consecutivos=3,
                estado_emocional={"confianca": 0.65, "stress": 0.35, "motivacao": 0.80, "fadiga": 0.25},
                maturidade_juridica={"pensamento_sistemico": 0.5, "capacidade_abstrair": 0.4, "dominio_terminologia": 0.6, "raciocinio_analogico": 0.45, "interpretacao_legal": 0.5},
                padroes_aprendizagem={"estilo_aprendizagem": "VISUAL", "velocidade_leitura": "MEDIA", "preferencia_explicacao": ["DIDATICA", "PRATICA"], "melhor_horario": "NOITE", "sessao_ideal_minutos": 45},
                riscos={"risco_evasao": 0.15, "risco_burnout": 0.10, "dias_seguidos_estudo": 3, "ultima_quebra_streak": None},
                metas={"data_prova_alvo": "2026-04-15", "ritmo_necessario_questoes_dia": 15, "ritmo_real_questoes_dia": 10, "topicos_prioritarios": ["Direito Penal", "Direito Civil"], "objetivo_pontuacao": 700}
            )
            db.add(perfil)
            print(f"  Criado: nivel={perfil.nivel_geral.value}, pontos={perfil.pontuacao_global}")

        db.flush()

        # ================================================================
        # 3. VERIFICAR QUESTOES NO BANCO
        # ================================================================
        print("\n[3/5] Verificando questoes no questoes_banco...")

        total_questoes = db.query(QuestaoBanco).filter(QuestaoBanco.ativa == True).count()
        print(f"  Questoes ativas em questoes_banco: {total_questoes}")

        if total_questoes < 5:
            print("  AVISO: Menos de 5 questoes no banco!")
            print("  Execute primeiro: POST /admin/seed-questoes")
            print("  Ou: python scripts/migrate_questoes.py")
            print("  Continuando sem sessoes/interacoes...")
            db.commit()
            _print_credentials(tester)
            return

        # Buscar questoes para usar nas sessoes
        questoes = db.query(QuestaoBanco).filter(
            QuestaoBanco.ativa == True
        ).limit(30).all()

        # ================================================================
        # 4. CRIAR 3 SESSOES DE ESTUDO COMPLETAS
        # ================================================================
        print("\n[4/5] Criando sessoes de estudo...")

        sessoes_config = [
            {"dias_atras": 3, "num_questoes": 10, "acertos": 7, "duracao": 25},
            {"dias_atras": 2, "num_questoes": 15, "acertos": 10, "duracao": 40},
            {"dias_atras": 1, "num_questoes": 10, "acertos": 8, "duracao": 30},
        ]

        # Limpar sessoes anteriores do tester (para evitar duplicatas no re-seed)
        sessoes_existentes = db.query(SessaoEstudo).filter(
            SessaoEstudo.user_id == tester.id,
            SessaoEstudo.fim != None
        ).count()

        if sessoes_existentes >= 3:
            print(f"  Ja existem {sessoes_existentes} sessoes completas. Pulando criacao.")
        else:
            for i, config in enumerate(sessoes_config):
                inicio = datetime.utcnow() - timedelta(days=config["dias_atras"], hours=20)
                fim = inicio + timedelta(minutes=config["duracao"])
                taxa = round((config["acertos"] / config["num_questoes"]) * 100, 1)

                sessao = SessaoEstudo(
                    user_id=tester.id,
                    inicio=inicio,
                    fim=fim,
                    duracao_minutos=config["duracao"],
                    modo_estudo="drill",
                    disciplinas_estudadas={"disciplinas": ["Direito Penal", "Direito Civil"]},
                    total_questoes=config["num_questoes"],
                    questoes_corretas=config["acertos"],
                    taxa_acerto_sessao=taxa,
                    estado_emocional_inicio={"confianca": 0.5, "motivacao": 0.7},
                    estado_emocional_fim={"confianca": 0.6, "motivacao": 0.75},
                    qualidade_sessao=round(taxa / 100, 2)
                )
                db.add(sessao)
                db.flush()

                # Criar interacoes para cada sessao
                num_q = min(config["num_questoes"], len(questoes))
                for j in range(num_q):
                    q = questoes[j % len(questoes)]
                    acertou = j < config["acertos"]
                    tipo = TipoResposta.CORRETA if acertou else TipoResposta.INCORRETA
                    escolhida = q.alternativa_correta if acertou else _alternativa_errada(q.alternativa_correta)

                    interacao = InteracaoQuestao(
                        user_id=tester.id,
                        questao_id=q.id,
                        sessao_estudo_id=sessao.id,
                        disciplina=q.disciplina,
                        topico=q.topico or "Geral",
                        tipo_resposta=tipo,
                        alternativa_escolhida=escolhida,
                        alternativa_correta=q.alternativa_correta,
                        tempo_resposta_segundos=30 + (j * 5)
                    )
                    db.add(interacao)

                print(f"  Sessao {i+1}: {config['num_questoes']}q, {config['acertos']} acertos ({taxa}%), {config['duracao']}min")

        db.flush()

        # ================================================================
        # 5. CRIAR PROGRESSO POR DISCIPLINA
        # ================================================================
        print("\n[5/5] Criando progresso por disciplina...")

        disciplinas_seed = [
            {"disciplina": "Direito Penal", "total": 15, "corretas": 11, "nivel": NivelDominio.INTERMEDIARIO, "prioridade": 3},
            {"disciplina": "Direito Civil", "total": 12, "corretas": 8, "nivel": NivelDominio.BASICO, "prioridade": 2},
            {"disciplina": "Direito Constitucional", "total": 8, "corretas": 6, "nivel": NivelDominio.INTERMEDIARIO, "prioridade": 4},
            {"disciplina": "Etica Profissional", "total": 5, "corretas": 4, "nivel": NivelDominio.BASICO, "prioridade": 6},
            {"disciplina": "Direito Processual Civil", "total": 5, "corretas": 2, "nivel": NivelDominio.INICIANTE, "prioridade": 1},
        ]

        for d in disciplinas_seed:
            existing_prog = db.query(ProgressoDisciplina).filter(
                ProgressoDisciplina.user_id == tester.id,
                ProgressoDisciplina.disciplina == d["disciplina"]
            ).first()

            taxa = round((d["corretas"] / d["total"]) * 100, 1)

            if existing_prog:
                existing_prog.total_questoes = d["total"]
                existing_prog.questoes_corretas = d["corretas"]
                existing_prog.taxa_acerto = taxa
                existing_prog.nivel_dominio = d["nivel"]
                existing_prog.prioridade_estudo = d["prioridade"]
                print(f"  Atualizado: {d['disciplina']} -> {taxa}% ({d['nivel'].value})")
            else:
                prog = ProgressoDisciplina(
                    user_id=tester.id,
                    disciplina=d["disciplina"],
                    total_questoes=d["total"],
                    questoes_corretas=d["corretas"],
                    taxa_acerto=taxa,
                    nivel_dominio=d["nivel"],
                    prioridade_estudo=d["prioridade"],
                    tempo_total_minutos=d["total"] * 3,
                    distribuicao_dificuldade={
                        "FACIL": {"total": d["total"] // 3, "acertos": d["corretas"] // 3},
                        "MEDIO": {"total": d["total"] // 2, "acertos": d["corretas"] // 2},
                        "DIFICIL": {"total": d["total"] - d["total"] // 3 - d["total"] // 2, "acertos": max(0, d["corretas"] - d["corretas"] // 3 - d["corretas"] // 2)},
                        "MUITO_DIFICIL": {"total": 0, "acertos": 0}
                    },
                    ultima_questao_respondida=datetime.utcnow() - timedelta(days=1)
                )
                db.add(prog)
                print(f"  Criado: {d['disciplina']} -> {taxa}% ({d['nivel'].value})")

        # Commit final
        db.commit()
        print("\n  Commit realizado com sucesso!")

        _print_credentials(tester)

    except Exception as e:
        db.rollback()
        print(f"\nERRO: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def _alternativa_errada(correta: str) -> str:
    """Retorna uma alternativa errada"""
    opcoes = ['A', 'B', 'C', 'D']
    opcoes.remove(correta.upper())
    return opcoes[0]


def _print_credentials(tester):
    """Imprime credenciais de acesso"""
    print("\n" + "=" * 70)
    print("SEED CONCLUIDO - CREDENCIAIS DO TESTER")
    print("=" * 70)
    print(f"""
  Email:  {TESTER_EMAIL}
  Senha:  {TESTER_SENHA}
  ID:     {tester.id}

  Fluxo de teste:
    1. POST /auth/login  -> obter token
    2. GET  /auth/me     -> ver perfil
    3. POST /api/sessao/iniciar   -> iniciar estudo
    4. POST /api/sessao/responder -> responder questoes
    5. POST /api/sessao/finalizar -> ver resultado
    6. GET  /api/progresso        -> dashboard
    7. GET  /api/progresso/disciplinas -> por disciplina
    8. GET  /api/progresso/ranking     -> leaderboard
""")
    print("=" * 70)


if __name__ == "__main__":
    seed()
