#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para popular banco de dados com dados de exemplo realistas

Cria:
- 10 usuários fake
- Progresso em várias disciplinas
- Interações com questões
- Simulados completados
- Dados de gamificação (streaks, XP)
"""

import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_db_session
from database.models import (
    User, PerfilJuridico, ProgressoDisciplina, ProgressoTopico,
    InteracaoQuestao, QuestaoBanco, SessaoEstudo,
    NivelDominio, DificuldadeQuestao, TipoResposta
)
from sqlalchemy import func

print("=" * 70)
print("SEED DATABASE - DOUTORA IA OAB")
print("=" * 70)

# Dados realistas
NOMES = [
    "Maria Silva", "João Santos", "Ana Costa", "Pedro Oliveira",
    "Juliana Souza", "Carlos Ferreira", "Beatriz Lima", "Lucas Almeida",
    "Fernanda Rocha", "Rafael Mendes"
]

DISCIPLINAS_OAB = [
    "Direito Civil", "Direito Penal", "Direito Constitucional",
    "Direito Processual Civil", "Direito Processual Penal",
    "Direito do Trabalho", "Direito Tributário", "Direito Empresarial",
    "Direito Administrativo", "Ética Profissional"
]

TOPICOS_POR_DISCIPLINA = {
    "Direito Civil": ["Obrigações", "Contratos", "Família", "Sucessões", "Responsabilidade Civil"],
    "Direito Penal": ["Parte Geral", "Crimes contra a pessoa", "Crimes contra o patrimônio", "Lei de Drogas"],
    "Direito Constitucional": ["Direitos Fundamentais", "Organização do Estado", "Controle de Constitucionalidade"],
    "Direito Processual Civil": ["Procedimento Comum", "Recursos", "Tutelas Provisórias"],
    "Direito Processual Penal": ["Inquérito", "Ação Penal", "Provas", "Prisões"],
    "Direito do Trabalho": ["CLT", "Contrato de Trabalho", "Direitos Trabalhistas"],
    "Direito Tributário": ["Impostos", "Taxas", "Contribuições", "CTN"],
    "Direito Empresarial": ["Sociedades", "Falência", "Títulos de Crédito"],
    "Direito Administrativo": ["Atos Administrativos", "Licitações", "Servidores Públicos"],
    "Ética Profissional": ["Estatuto da OAB", "Código de Ética", "Infrações Disciplinares"]
}

def criar_usuario_fake(index):
    """Cria um usuário fake com dados realistas"""
    nome = NOMES[index]
    email = nome.lower().replace(" ", ".") + "@exemplo.com"

    user = User(
        id=uuid4(),
        nome=nome,
        email=email,
        password_hash="$2b$12$dummy_hash_para_teste",  # Hash fake
        plano="GRATUITO" if index < 7 else "PREMIUM",
        criado_em=datetime.now() - timedelta(days=random.randint(10, 90)),
        ativo=True
    )

    return user

def criar_perfil_juridico(user):
    """Cria perfil jurídico do usuário"""
    # Nível baseado em tempo de uso
    dias_uso = (datetime.now() - user.criado_em).days
    if dias_uso < 30:
        nivel = NivelDominio.INICIANTE
    elif dias_uso < 60:
        nivel = NivelDominio.INTERMEDIARIO
    else:
        nivel = NivelDominio.AVANCADO

    perfil = PerfilJuridico(
        id=uuid4(),
        user_id=user.id,
        nivel_geral=nivel,
        total_questoes_respondidas=random.randint(50, 500),
        taxa_acerto_geral=random.uniform(50, 90),
        tempo_total_estudo_minutos=random.randint(300, 3000),
        streak_atual=random.randint(0, 15),
        streak_maximo=random.randint(5, 30),
        xp_total=random.randint(500, 5000),
        nivel_xp=random.randint(1, 10)
    )

    return perfil

def criar_progresso_disciplina(user, disciplina):
    """Cria progresso realista em uma disciplina"""
    # Variar desempenho por disciplina
    taxa_base = random.uniform(40, 85)
    total_q = random.randint(10, 100)
    acertos = int(total_q * (taxa_base / 100))

    # Determinar nível baseado na taxa de acerto
    if taxa_base < 50:
        nivel = NivelDominio.INICIANTE
    elif taxa_base < 70:
        nivel = NivelDominio.INTERMEDIARIO
    else:
        nivel = NivelDominio.AVANCADO

    progresso = ProgressoDisciplina(
        id=uuid4(),
        user_id=user.id,
        disciplina=disciplina,
        nivel_dominio=nivel,
        taxa_acerto=taxa_base,
        total_questoes=total_q,
        questoes_corretas=acertos,
        tempo_total_minutos=total_q * random.randint(2, 5),
        peso_prova_oab=1.0,
        prioridade_estudo=random.randint(1, 10),
        distribuicao_dificuldade={
            "FACIL": {"total": random.randint(5, 20), "acertos": random.randint(4, 18)},
            "MEDIO": {"total": random.randint(10, 40), "acertos": random.randint(5, 30)},
            "DIFICIL": {"total": random.randint(3, 15), "acertos": random.randint(1, 10)}
        },
        ultima_questao_em=datetime.now() - timedelta(days=random.randint(0, 7))
    )

    return progresso

def criar_progresso_topico(user, disciplina, topico):
    """Cria progresso em um tópico específico"""
    taxa = random.uniform(40, 90)
    total = random.randint(5, 30)
    acertos = int(total * (taxa / 100))

    if taxa < 50:
        nivel = NivelDominio.INICIANTE
    elif taxa < 70:
        nivel = NivelDominio.INTERMEDIARIO
    else:
        nivel = NivelDominio.AVANCADO

    progresso = ProgressoTopico(
        id=uuid4(),
        user_id=user.id,
        disciplina=disciplina,
        topico=topico,
        nivel_dominio=nivel,
        taxa_acerto=taxa,
        total_questoes=total,
        questoes_corretas=acertos,
        fator_retencao=random.uniform(0.3, 0.9),
        intervalo_revisao_dias=random.choice([1, 3, 7, 15, 30]),
        numero_revisoes=random.randint(0, 5),
        erros_recorrentes=[],
        conceitos_criticos=[],
        proxima_revisao=datetime.now() + timedelta(days=random.randint(1, 30))
    )

    return progresso

def criar_interacao_questao(user, questao_id, acertou):
    """Cria interação com uma questão"""
    alternativas = ['A', 'B', 'C', 'D']

    interacao = InteracaoQuestao(
        id=uuid4(),
        user_id=user.id,
        questao_id=questao_id,
        alternativa_escolhida=random.choice(alternativas),
        tipo_resposta=TipoResposta.CORRETA if acertou else TipoResposta.INCORRETA,
        tempo_resposta_segundos=random.randint(60, 300),
        timestamp=datetime.now() - timedelta(days=random.randint(0, 30))
    )

    return interacao

def criar_sessao_estudo(user):
    """Cria uma sessão de estudo"""
    sessao = SessaoEstudo(
        id=uuid4(),
        user_id=user.id,
        tipo_sessao="drill",
        disciplina_foco=random.choice(DISCIPLINAS_OAB),
        quantidade_questoes=random.randint(10, 20),
        iniciada_em=datetime.now() - timedelta(days=random.randint(1, 30)),
        finalizada_em=datetime.now() - timedelta(days=random.randint(1, 30)) + timedelta(hours=1),
        concluida=True
    )

    return sessao

def main():
    print("\n[1/6] Verificando questões no banco...")

    with get_db_session() as session:
        total_questoes = session.query(func.count(QuestaoBanco.id)).scalar()
        print(f"Total de questões disponíveis: {total_questoes}")

        if total_questoes < 100:
            print("AVISO: Poucas questões no banco. Recomenda-se ter pelo menos 1000 questões.")

        # Buscar IDs de questões para criar interações
        questoes_ids = [q.id for q in session.query(QuestaoBanco.id).limit(500).all()]
        print(f"Usando {len(questoes_ids)} questões para criar interações")

    print("\n[2/6] Criando usuários fake...")
    usuarios_criados = []

    with get_db_session() as session:
        for i in range(10):
            user = criar_usuario_fake(i)
            session.add(user)
            usuarios_criados.append(user)
            print(f"  ✓ {user.nome} ({user.email}) - Plano: {user.plano}")

        session.commit()
        print(f"\n✅ {len(usuarios_criados)} usuários criados")

    print("\n[3/6] Criando perfis jurídicos...")

    with get_db_session() as session:
        for user in usuarios_criados:
            perfil = criar_perfil_juridico(user)
            session.add(perfil)
            print(f"  ✓ {user.nome} - Nível: {perfil.nivel_geral.value}, XP: {perfil.xp_total}")

        session.commit()
        print(f"\n✅ Perfis criados")

    print("\n[4/6] Criando progresso por disciplina...")

    with get_db_session() as session:
        for user in usuarios_criados:
            # Cada usuário estuda entre 5-10 disciplinas
            num_disciplinas = random.randint(5, 10)
            disciplinas_user = random.sample(DISCIPLINAS_OAB, num_disciplinas)

            for disciplina in disciplinas_user:
                progresso = criar_progresso_disciplina(user, disciplina)
                session.add(progresso)

            print(f"  ✓ {user.nome} - {num_disciplinas} disciplinas")

        session.commit()
        print(f"\n✅ Progresso por disciplina criado")

    print("\n[5/6] Criando progresso por tópico...")

    with get_db_session() as session:
        for user in usuarios_criados:
            # Para cada disciplina que o usuário estuda
            progressos_disc = session.query(ProgressoDisciplina).filter(
                ProgressoDisciplina.user_id == user.id
            ).all()

            total_topicos = 0
            for prog_disc in progressos_disc:
                topicos = TOPICOS_POR_DISCIPLINA.get(prog_disc.disciplina, [])
                # Estudar 2-4 tópicos por disciplina
                num_topicos = min(random.randint(2, 4), len(topicos))
                topicos_user = random.sample(topicos, num_topicos)

                for topico in topicos_user:
                    prog_topico = criar_progresso_topico(user, prog_disc.disciplina, topico)
                    session.add(prog_topico)
                    total_topicos += 1

            print(f"  ✓ {user.nome} - {total_topicos} tópicos")

        session.commit()
        print(f"\n✅ Progresso por tópico criado")

    print("\n[6/6] Criando interações com questões...")

    if len(questoes_ids) > 0:
        with get_db_session() as session:
            for user in usuarios_criados:
                # Cada usuário responde entre 50-200 questões
                num_questoes = random.randint(50, min(200, len(questoes_ids)))
                questoes_user = random.sample(questoes_ids, num_questoes)

                for questao_id in questoes_user:
                    # Taxa de acerto realista (50-80%)
                    acertou = random.random() < random.uniform(0.5, 0.8)
                    interacao = criar_interacao_questao(user, questao_id, acertou)
                    session.add(interacao)

                print(f"  ✓ {user.nome} - {num_questoes} questões respondidas")

            session.commit()
            print(f"\n✅ Interações criadas")
    else:
        print("\n⚠️ Sem questões disponíveis, pulando criação de interações")

    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)

    with get_db_session() as session:
        total_users = session.query(func.count(User.id)).scalar()
        total_perfis = session.query(func.count(PerfilJuridico.id)).scalar()
        total_prog_disc = session.query(func.count(ProgressoDisciplina.id)).scalar()
        total_prog_top = session.query(func.count(ProgressoTopico.id)).scalar()
        total_interacoes = session.query(func.count(InteracaoQuestao.id)).scalar()

        print(f"Usuários: {total_users}")
        print(f"Perfis: {total_perfis}")
        print(f"Progresso Disciplinas: {total_prog_disc}")
        print(f"Progresso Tópicos: {total_prog_top}")
        print(f"Interações: {total_interacoes}")

    print("\n✅ SEED COMPLETO!")
    print("=" * 70)

if __name__ == "__main__":
    main()
