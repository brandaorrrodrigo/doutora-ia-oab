"""
================================================================================
JURIS_IA_CORE_V1 - Serviço de Explicações com LLM
================================================================================
Objetivo: Gerar explicações pedagógicas personalizadas usando OpenAI GPT-4o-mini
Prioridade: P0 (CRÍTICA)
Data: 2025-12-17
================================================================================
"""

import os
import json
import logging
import hashlib
from typing import Dict, Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExplicacaoService:
    """
    Serviço de geração de explicações pedagógicas com LLM.

    Usa GPT-4o-mini para gerar explicações personalizadas sobre:
    - Por que a alternativa escolhida está incorreta
    - Por que a alternativa correta está correta
    - Conceito jurídico central
    - Norma legal aplicável
    """

    # Modelo LLM
    LLM_MODEL = "gpt-4o-mini"
    MAX_TOKENS = 300
    TEMPERATURE = 0.3  # Baixa temperatura para respostas mais precisas

    # Cache de explicações
    CACHE_TTL_DAYS = 30  # Explicações em cache por 30 dias

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o serviço de explicações.

        Args:
            api_key: Chave da API OpenAI (se None, usa variável de ambiente)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key da OpenAI não encontrada. "
                "Defina OPENAI_API_KEY na variável de ambiente."
            )

        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"ExplicacaoService inicializado com modelo {self.LLM_MODEL}")


    def _gerar_cache_key(
        self,
        questao_id: UUID,
        alternativa_escolhida: str,
        tipo_erro: str
    ) -> str:
        """
        Gera chave única para cache de explicação.

        Args:
            questao_id: ID da questão
            alternativa_escolhida: Alternativa escolhida pelo usuário
            tipo_erro: Tipo de erro cometido

        Returns:
            Hash MD5 para usar como chave de cache
        """
        chave = f"{questao_id}_{alternativa_escolhida}_{tipo_erro}"
        return hashlib.md5(chave.encode()).hexdigest()


    def _buscar_explicacao_cache(
        self,
        session: Session,
        cache_key: str
    ) -> Optional[str]:
        """
        Busca explicação no cache.

        Args:
            session: Sessão do SQLAlchemy
            cache_key: Chave de cache

        Returns:
            Explicação se encontrada no cache, None caso contrário
        """
        try:
            result = session.execute(
                text("""
                    SELECT explicacao
                    FROM cache_explicacao
                    WHERE cache_key = :cache_key
                      AND expires_at > NOW()
                """),
                {"cache_key": cache_key}
            ).fetchone()

            if result:
                logger.debug(f"Explicação encontrada no cache: {cache_key}")
                return result[0]

            return None

        except Exception as e:
            logger.warning(f"Erro ao buscar cache: {e}")
            return None


    def _salvar_explicacao_cache(
        self,
        session: Session,
        cache_key: str,
        explicacao: str
    ) -> None:
        """
        Salva explicação no cache.

        Args:
            session: Sessão do SQLAlchemy
            cache_key: Chave de cache
            explicacao: Texto da explicação
        """
        try:
            expires_at = datetime.now() + timedelta(days=self.CACHE_TTL_DAYS)

            session.execute(
                text("""
                    INSERT INTO cache_explicacao (
                        cache_key, explicacao, expires_at, created_at
                    ) VALUES (
                        :cache_key, :explicacao, :expires_at, NOW()
                    )
                    ON CONFLICT (cache_key) DO UPDATE
                    SET explicacao = EXCLUDED.explicacao,
                        expires_at = EXCLUDED.expires_at,
                        acessos = cache_explicacao.acessos + 1
                """),
                {
                    "cache_key": cache_key,
                    "explicacao": explicacao,
                    "expires_at": expires_at
                }
            )

            session.commit()
            logger.debug(f"Explicação salva no cache: {cache_key}")

        except Exception as e:
            session.rollback()
            logger.warning(f"Erro ao salvar cache: {e}")


    def _construir_prompt(
        self,
        enunciado: str,
        alternativas: Dict[str, str],
        alternativa_escolhida: str,
        alternativa_correta: str,
        tipo_erro: str,
        comentario_professor: Optional[str] = None,
        disciplina: Optional[str] = None,
        assunto: Optional[str] = None,
        nivel_usuario: Optional[str] = None
    ) -> str:
        """
        Constrói o prompt para o LLM.

        Args:
            enunciado: Enunciado da questão
            alternativas: Dict com alternativas
            alternativa_escolhida: Alternativa escolhida pelo usuário
            alternativa_correta: Alternativa correta
            tipo_erro: Tipo de erro cometido
            comentario_professor: Comentário opcional do professor
            disciplina: Disciplina da questão
            assunto: Assunto específico
            nivel_usuario: Nível do usuário (iniciante, intermediario, avancado)

        Returns:
            Prompt formatado
        """
        # Formatar alternativas
        alternativas_texto = "\n".join([
            f"{letra}) {texto}"
            for letra, texto in sorted(alternativas.items())
        ])

        # Texto sobre o tipo de erro
        tipo_erro_descricao = {
            "conceito": "confusão conceitual",
            "norma": "aplicação incorreta da norma",
            "interpretacao": "erro de interpretação",
            "desatencao": "desatenção ao enunciado"
        }.get(tipo_erro, "erro")

        # Adaptar ao nível do usuário
        if nivel_usuario == "iniciante":
            nivel_instrucao = "Use linguagem simples e didática, como se estivesse ensinando pela primeira vez."
        elif nivel_usuario == "avancado":
            nivel_instrucao = "Seja mais técnico e aprofundado nos conceitos jurídicos."
        else:
            nivel_instrucao = "Use linguagem clara mas técnica, apropriada para estudantes de Direito."

        # Construir prompt
        prompt = f"""Você é um professor especialista em Direito para preparação para o Exame da OAB.

QUESTÃO:
{enunciado}

ALTERNATIVAS:
{alternativas_texto}

SITUAÇÃO:
O aluno escolheu a alternativa {alternativa_escolhida}, mas a correta é a alternativa {alternativa_correta}.
Tipo de erro: {tipo_erro_descricao}
"""

        if disciplina:
            prompt += f"Disciplina: {disciplina}\n"

        if assunto:
            prompt += f"Assunto: {assunto}\n"

        if comentario_professor:
            prompt += f"\nCOMENTÁRIO DO PROFESSOR:\n{comentario_professor}\n"

        prompt += f"""
TAREFA:
Gere uma explicação pedagógica concisa (máximo 250 palavras) que:

1. Explique por que a alternativa {alternativa_escolhida} está INCORRETA
2. Explique por que a alternativa {alternativa_correta} está CORRETA
3. Reforce o conceito jurídico central da questão
4. Cite a norma legal aplicável (artigo específico)

{nivel_instrucao}

FORMATO:
Use parágrafos curtos e objetivos. Seja direto e didático."""

        return prompt


    def gerar_explicacao_erro(
        self,
        session: Session,
        questao_id: UUID,
        alternativa_escolhida: str,
        tipo_erro: str = "conceito",
        usar_cache: bool = True,
        nivel_usuario: str = "intermediario"
    ) -> Tuple[Optional[str], Dict]:
        """
        Gera explicação personalizada para erro do usuário.

        Args:
            session: Sessão do SQLAlchemy
            questao_id: ID da questão
            alternativa_escolhida: Alternativa escolhida pelo usuário
            tipo_erro: Tipo de erro cometido
            usar_cache: Se True, tenta buscar no cache primeiro
            nivel_usuario: Nível do usuário para adaptar explicação

        Returns:
            Tupla (explicacao, metadados)
        """
        try:
            inicio = datetime.now()

            # Buscar dados da questão
            result = session.execute(
                text("""
                    SELECT
                        q.enunciado,
                        q.alternativas,
                        g.alternativa_correta,
                        q.comentario_professor,
                        q.disciplina,
                        q.assunto
                    FROM questao_oab q
                    JOIN gabarito_questao g ON q.id = g.questao_id
                    WHERE q.id = :id
                """),
                {"id": questao_id}
            ).fetchone()

            if not result:
                logger.error(f"Questão {questao_id} não encontrada")
                return None, {"erro": "Questão não encontrada"}

            (enunciado, alternativas, alternativa_correta,
             comentario_professor, disciplina, assunto) = result

            # Verificar se já está correta
            if alternativa_escolhida == alternativa_correta:
                logger.info("Alternativa escolhida está correta, sem necessidade de explicação de erro")
                return None, {"info": "Resposta correta"}

            # Tentar cache
            cache_key = self._gerar_cache_key(
                questao_id,
                alternativa_escolhida,
                tipo_erro
            )

            if usar_cache:
                explicacao_cache = self._buscar_explicacao_cache(session, cache_key)
                if explicacao_cache:
                    tempo_total = (datetime.now() - inicio).total_seconds()
                    return explicacao_cache, {
                        "fonte": "cache",
                        "tempo_ms": int(tempo_total * 1000),
                        "custo_estimado": 0
                    }

            # Construir prompt
            prompt = self._construir_prompt(
                enunciado=enunciado,
                alternativas=alternativas,
                alternativa_escolhida=alternativa_escolhida,
                alternativa_correta=alternativa_correta,
                tipo_erro=tipo_erro,
                comentario_professor=comentario_professor,
                disciplina=disciplina,
                assunto=assunto,
                nivel_usuario=nivel_usuario
            )

            # Gerar explicação com LLM
            logger.info(f"Gerando explicação via LLM para questão {questao_id}")

            response = self.client.chat.completions.create(
                model=self.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um professor especialista em Direito para preparação OAB."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.MAX_TOKENS,
                temperature=self.TEMPERATURE
            )

            explicacao = response.choices[0].message.content.strip()

            # Salvar em cache
            if usar_cache:
                self._salvar_explicacao_cache(session, cache_key, explicacao)

            # Calcular custo estimado
            tokens_usados = response.usage.total_tokens
            # gpt-4o-mini: $0.00015 / 1K input tokens, $0.0006 / 1K output tokens
            custo_input = (response.usage.prompt_tokens / 1000) * 0.00015
            custo_output = (response.usage.completion_tokens / 1000) * 0.0006
            custo_total = custo_input + custo_output

            # Metadados
            tempo_total = (datetime.now() - inicio).total_seconds()
            metadados = {
                "fonte": "llm",
                "modelo": self.LLM_MODEL,
                "tempo_ms": int(tempo_total * 1000),
                "tokens_usados": tokens_usados,
                "custo_estimado": round(custo_total, 6)
            }

            logger.info(
                f"Explicação gerada: {tokens_usados} tokens, "
                f"${custo_total:.6f}, {tempo_total:.2f}s"
            )

            return explicacao, metadados

        except Exception as e:
            logger.error(f"Erro ao gerar explicação: {e}")
            return None, {"erro": str(e)}


    def gerar_dica_pre_resposta(
        self,
        session: Session,
        questao_id: UUID,
        nivel_usuario: str = "intermediario"
    ) -> Optional[str]:
        """
        Gera dica pedagógica ANTES do usuário responder.

        Útil para questões difíceis ou quando usuário solicita ajuda.

        Args:
            session: Sessão do SQLAlchemy
            questao_id: ID da questão
            nivel_usuario: Nível do usuário

        Returns:
            Dica pedagógica (sem revelar a resposta)
        """
        try:
            # Buscar questão (SEM gabarito)
            result = session.execute(
                text("""
                    SELECT
                        enunciado,
                        alternativas,
                        disciplina,
                        assunto,
                        dificuldade
                    FROM questao_oab
                    WHERE id = :id
                """),
                {"id": questao_id}
            ).fetchone()

            if not result:
                return None

            enunciado, alternativas, disciplina, assunto, dificuldade = result

            # Formatar alternativas
            alternativas_texto = "\n".join([
                f"{letra}) {texto}"
                for letra, texto in sorted(alternativas.items())
            ])

            # Prompt para dica
            prompt = f"""Você é um professor de Direito preparando um aluno para o Exame da OAB.

QUESTÃO:
{enunciado}

ALTERNATIVAS:
{alternativas_texto}

Disciplina: {disciplina}
Assunto: {assunto}
Dificuldade: {dificuldade}

TAREFA:
Dê uma DICA pedagógica que ajude o aluno a RACIOCINAR sobre a questão, mas SEM REVELAR a resposta correta.

A dica deve:
- Indicar o conceito jurídico central
- Citar a norma legal aplicável
- Sugerir o raciocínio a seguir
- Alertar sobre possíveis pegadinhas

Máximo 150 palavras. Seja objetivo e didático."""

            response = self.client.chat.completions.create(
                model=self.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um professor de Direito."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.4
            )

            dica = response.choices[0].message.content.strip()

            logger.info(f"Dica gerada para questão {questao_id}")
            return dica

        except Exception as e:
            logger.error(f"Erro ao gerar dica: {e}")
            return None


    def analisar_padroes_erro(
        self,
        session: Session,
        usuario_id: UUID,
        limite_respostas: int = 20
    ) -> Dict:
        """
        Analisa padrões de erro do usuário e gera relatório com LLM.

        Args:
            session: Sessão do SQLAlchemy
            usuario_id: ID do usuário
            limite_respostas: Número de respostas recentes a analisar

        Returns:
            Dict com análise dos padrões de erro
        """
        try:
            # Buscar erros recentes do usuário
            erros = session.execute(
                text("""
                    SELECT
                        q.disciplina,
                        q.assunto,
                        r.tipo_erro,
                        COUNT(*) as qtd_erros
                    FROM resposta r
                    JOIN questao_oab q ON r.questao_id = q.id
                    WHERE r.usuario_id = :usuario_id
                      AND r.correta = FALSE
                      AND r.respondida_em >= NOW() - INTERVAL '30 days'
                    GROUP BY q.disciplina, q.assunto, r.tipo_erro
                    ORDER BY qtd_erros DESC
                    LIMIT :limite
                """),
                {"usuario_id": usuario_id, "limite": limite_respostas}
            ).fetchall()

            if not erros:
                return {"analise": "Nenhum erro recente para analisar"}

            # Formatar erros para análise
            erros_texto = "\n".join([
                f"- {row[0]} ({row[1]}): {row[3]} erros do tipo '{row[2]}'"
                for row in erros
            ])

            # Prompt para análise
            prompt = f"""Você é um professor de Direito analisando o desempenho de um aluno preparando para a OAB.

PADRÕES DE ERRO (últimos 30 dias):
{erros_texto}

TAREFA:
Analise os padrões de erro e forneça:

1. Principais áreas de dificuldade
2. Tipo de erro mais comum (conceitual, normativo, interpretação)
3. Recomendações específicas de estudo
4. Tópicos prioritários para revisão

Seja específico, prático e encorajador. Máximo 200 palavras."""

            response = self.client.chat.completions.create(
                model=self.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um professor de Direito."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.3
            )

            analise = response.choices[0].message.content.strip()

            return {
                "analise": analise,
                "erros_analisados": len(erros),
                "gerado_em": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Erro ao analisar padrões: {e}")
            return {"erro": str(e)}


# ================================================================================
# MIGRAÇÃO PARA TABELA DE CACHE
# ================================================================================

SQL_CREATE_CACHE_TABLE = """
-- Tabela de cache de explicações
CREATE TABLE IF NOT EXISTS cache_explicacao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(32) UNIQUE NOT NULL,
    explicacao TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    acessos INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_cache_explicacao_key ON cache_explicacao(cache_key);
CREATE INDEX idx_cache_explicacao_expires ON cache_explicacao(expires_at);

-- Trigger de updated_at
CREATE TRIGGER trigger_cache_explicacao_updated_at
    BEFORE UPDATE ON cache_explicacao
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

-- Comentário
COMMENT ON TABLE cache_explicacao IS 'Cache de explicações geradas por LLM';
"""


def criar_tabela_cache(session: Session) -> bool:
    """
    Cria tabela de cache de explicações se não existir.

    Args:
        session: Sessão do SQLAlchemy

    Returns:
        True se criada com sucesso
    """
    try:
        session.execute(text(SQL_CREATE_CACHE_TABLE))
        session.commit()
        logger.info("Tabela cache_explicacao criada com sucesso")
        return True

    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao criar tabela de cache: {e}")
        return False


def limpar_cache_expirado(session: Session) -> int:
    """
    Remove explicações expiradas do cache.

    Args:
        session: Sessão do SQLAlchemy

    Returns:
        Número de registros removidos
    """
    try:
        result = session.execute(
            text("""
                DELETE FROM cache_explicacao
                WHERE expires_at < NOW()
            """)
        )

        session.commit()
        removidos = result.rowcount

        logger.info(f"{removidos} explicações expiradas removidas do cache")
        return removidos

    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao limpar cache: {e}")
        return 0
