"""
================================================================================
JURIS_IA_CORE_V1 - Serviço de Explicações com OLLAMA/LLAMA (IA Própria)
================================================================================
Objetivo: Gerar explicações pedagógicas usando Llama local via Ollama
Prioridade: P0 (CRÍTICA)
Data: 2025-12-17
================================================================================

MODELOS RECOMENDADOS PARA EXPLICAÇÕES:
- llama3.2:3b - Rápido, 3B parâmetros, ~2GB RAM
- llama3.1:8b - Balanceado, 8B parâmetros, ~5GB RAM
- llama3:70b - Melhor qualidade, 70B parâmetros, ~40GB RAM (quantizado)

VANTAGENS OLLAMA/LLAMA:
- Custo ZERO de API
- Dados 100% privados
- Sem limites de rate limiting
- Latência previsível

REQUISITOS:
- Ollama instalado e rodando
- Modelo Llama baixado (ollama pull llama3.2:3b)
- 4GB+ RAM para modelos menores
- GPU recomendada (CUDA/ROCm) para melhor performance

================================================================================
"""

import logging
import requests
import json
import hashlib
from typing import Dict, Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExplicacaoServiceOllama:
    """
    Serviço de geração de explicações pedagógicas com Llama local.

    Usa modelos Llama rodando localmente via Ollama para:
    - Explicações de erros
    - Dicas pré-resposta
    - Análise de padrões
    """

    # Configuração do modelo
    DEFAULT_MODEL = "llama3.2:3b"  # Modelo padrão (rápido)
    DEFAULT_HOST = "http://localhost:11434"

    # Parâmetros de geração
    MAX_TOKENS = 300
    TEMPERATURE = 0.3  # Baixa temperatura para respostas mais precisas

    # Cache de explicações
    CACHE_TTL_DAYS = 30

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        ollama_host: str = DEFAULT_HOST
    ):
        """
        Inicializa o serviço de explicações com Ollama.

        Args:
            model: Nome do modelo Llama
            ollama_host: URL do servidor Ollama
        """
        self.model = model
        self.ollama_host = ollama_host

        # Verificar se Ollama está disponível
        if not self._verificar_ollama():
            raise ConnectionError(
                f"Ollama não está acessível em {ollama_host}. "
                "Certifique-se de que o servidor Ollama está rodando."
            )

        # Verificar se modelo está disponível
        if not self._verificar_modelo():
            logger.warning(
                f"Modelo {model} não encontrado. "
                f"Execute: ollama pull {model}"
            )

        logger.info(f"ExplicacaoServiceOllama inicializado com modelo {model}")


    def _verificar_ollama(self) -> bool:
        """
        Verifica se servidor Ollama está rodando.

        Returns:
            True se Ollama está acessível
        """
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Erro ao conectar ao Ollama: {e}")
            return False


    def _verificar_modelo(self) -> bool:
        """
        Verifica se modelo está disponível no Ollama.

        Returns:
            True se modelo está disponível
        """
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)

            if response.status_code == 200:
                modelos = response.json().get("models", [])
                modelos_disponiveis = [m["name"] for m in modelos]
                return self.model in modelos_disponiveis

            return False

        except Exception as e:
            logger.error(f"Erro ao verificar modelo: {e}")
            return False


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
        Constrói o prompt para o Llama.

        Args:
            enunciado: Enunciado da questão
            alternativas: Dict com alternativas
            alternativa_escolhida: Alternativa escolhida pelo usuário
            alternativa_correta: Alternativa correta
            tipo_erro: Tipo de erro cometido
            comentario_professor: Comentário opcional do professor
            disciplina: Disciplina da questão
            assunto: Assunto específico
            nivel_usuario: Nível do usuário

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
            nivel_instrucao = "Use linguagem simples e didática."
        elif nivel_usuario == "avancado":
            nivel_instrucao = "Seja técnico e aprofundado nos conceitos."
        else:
            nivel_instrucao = "Use linguagem clara mas técnica."

        # Construir prompt
        prompt = f"""Você é um professor de Direito especializado em preparação para o Exame da OAB.

QUESTÃO:
{enunciado}

ALTERNATIVAS:
{alternativas_texto}

SITUAÇÃO:
O aluno escolheu a alternativa {alternativa_escolhida}, mas a correta é {alternativa_correta}.
Tipo de erro: {tipo_erro_descricao}
"""

        if disciplina:
            prompt += f"Disciplina: {disciplina}\n"

        if assunto:
            prompt += f"Assunto: {assunto}\n"

        if comentario_professor:
            prompt += f"\nCOMENTÁRIO:\n{comentario_professor}\n"

        prompt += f"""
TAREFA:
Gere uma explicação pedagógica CONCISA (máximo 200 palavras) que:

1. Explique por que {alternativa_escolhida} está INCORRETA
2. Explique por que {alternativa_correta} está CORRETA
3. Reforce o conceito jurídico central
4. Cite a norma legal aplicável (artigo específico)

{nivel_instrucao}
Seja direto e objetivo. Use parágrafos curtos."""

        return prompt


    def _chamar_ollama(
        self,
        prompt: str,
        system_prompt: str = "Você é um professor de Direito."
    ) -> Tuple[str, Dict]:
        """
        Chama API do Ollama para gerar texto.

        Args:
            prompt: Prompt do usuário
            system_prompt: Prompt do sistema

        Returns:
            Tupla (texto_gerado, metadados)
        """
        try:
            inicio = datetime.now()

            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": self.TEMPERATURE,
                    "num_predict": self.MAX_TOKENS
                }
            }

            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=payload,
                timeout=60  # 1 minuto de timeout
            )

            if response.status_code != 200:
                raise Exception(
                    f"Ollama retornou status {response.status_code}: "
                    f"{response.text}"
                )

            resultado = response.json()
            texto = resultado.get("response", "").strip()

            # Metadados
            tempo_total = (datetime.now() - inicio).total_seconds()
            metadados = {
                "modelo": self.model,
                "tempo_s": tempo_total,
                "tokens_gerados": resultado.get("eval_count", 0),
                "tokens_prompt": resultado.get("prompt_eval_count", 0)
            }

            return texto, metadados

        except Exception as e:
            logger.error(f"Erro ao chamar Ollama: {e}")
            raise


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
            nivel_usuario: Nível do usuário

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
                        "custo": 0
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

            # Gerar explicação com Llama
            logger.info(f"Gerando explicação via Llama para questão {questao_id}")

            explicacao, meta_ollama = self._chamar_ollama(
                prompt=prompt,
                system_prompt="Você é um professor de Direito especializado em OAB."
            )

            # Salvar em cache
            if usar_cache:
                self._salvar_explicacao_cache(session, cache_key, explicacao)

            # Metadados
            tempo_total = (datetime.now() - inicio).total_seconds()
            metadados = {
                "fonte": "llama",
                "modelo": self.model,
                "tempo_ms": int(tempo_total * 1000),
                "tempo_geracao_s": meta_ollama["tempo_s"],
                "tokens_gerados": meta_ollama["tokens_gerados"],
                "custo": 0  # Custo zero (modelo local)
            }

            logger.info(
                f"Explicação gerada: {meta_ollama['tokens_gerados']} tokens, "
                f"{tempo_total:.2f}s"
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
            prompt = f"""Você é um professor de Direito.

QUESTÃO:
{enunciado}

ALTERNATIVAS:
{alternativas_texto}

Disciplina: {disciplina}
Assunto: {assunto}

TAREFA:
Dê uma DICA que ajude o aluno a RACIOCINAR, mas SEM REVELAR a resposta.

A dica deve:
- Indicar o conceito jurídico central
- Citar a norma legal aplicável
- Sugerir o raciocínio correto
- Alertar sobre possíveis pegadinhas

Máximo 120 palavras. Seja objetivo."""

            dica, _ = self._chamar_ollama(
                prompt=prompt,
                system_prompt="Você é um professor de Direito."
            )

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
        Analisa padrões de erro do usuário e gera relatório.

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
            prompt = f"""Você é um professor de Direito analisando o desempenho de um aluno.

PADRÕES DE ERRO (últimos 30 dias):
{erros_texto}

TAREFA:
Analise e forneça:

1. Principais áreas de dificuldade
2. Tipo de erro mais comum
3. Recomendações específicas de estudo
4. Tópicos prioritários para revisão

Máximo 180 palavras. Seja específico e encorajador."""

            analise, _ = self._chamar_ollama(
                prompt=prompt,
                system_prompt="Você é um professor de Direito."
            )

            return {
                "analise": analise,
                "erros_analisados": len(erros),
                "gerado_em": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Erro ao analisar padrões: {e}")
            return {"erro": str(e)}


# ================================================================================
# FUNÇÕES AUXILIARES
# ================================================================================

def listar_modelos_ollama(ollama_host: str = "http://localhost:11434") -> List[Dict]:
    """
    Lista modelos disponíveis no Ollama.

    Args:
        ollama_host: URL do servidor Ollama

    Returns:
        Lista de modelos disponíveis
    """
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)

        if response.status_code == 200:
            modelos = response.json().get("models", [])

            modelos_info = []
            for modelo in modelos:
                modelos_info.append({
                    "nome": modelo["name"],
                    "tamanho_gb": modelo.get("size", 0) / (1024**3),
                    "modificado": modelo.get("modified_at"),
                    "familia": modelo.get("details", {}).get("family", "")
                })

            return modelos_info

        return []

    except Exception as e:
        logger.error(f"Erro ao listar modelos: {e}")
        return []
