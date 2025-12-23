"""
JURIS_IA_CORE_V1 - PIPELINE DE INGESTÃO DA LEI SECA
Ingestão em lote de legislação brasileira com validação e logs.

Características:
- Execução em lote (batch processing)
- Idempotência total (rodar 2x não duplica)
- Logs completos de ingestão
- Validação por etapa
- Rollback automático em falha
- Performance otimizada

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
"""

import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from uuid import UUID, uuid4

# Adiciona path do projeto
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import get_db_session
from database.repositories import RepositoryFactory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

# ============================================================
# CONFIGURAÇÃO DE LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ingestao_lei_seca.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ============================================================
# CLASSES DE DADOS
# ============================================================

class UnidadeNormativa:
    """Representa uma unidade normativa para ingestão."""

    def __init__(self, data: Dict):
        self.diploma_legal = data['diploma_legal']
        self.nome_popular = data['nome_popular']
        self.artigo = data['artigo']
        self.paragrafo = data.get('paragrafo')
        self.inciso = data.get('inciso')
        self.alinea = data.get('alinea')
        self.texto_normativo = data['texto_normativo']

        # Classificação
        self.ramo_direito = data['ramo_direito']
        self.natureza_normativa = data['natureza_normativa']
        self.tipo_normativo = data['tipo_normativo']

        # Conceitual
        self.instituto_juridico_principal = data['instituto_juridico_principal']
        self.institutos_secundarios = data.get('institutos_secundarios', [])
        self.conceitos_chave = data['conceitos_chave']
        self.termos_tecnicos = data.get('termos_tecnicos', [])

        # Incidência
        self.incidencia_oab = data.get('incidencia_oab', {
            'frequencia_absoluta': 0,
            'frequencia_relativa': 0.0,
            'ultima_incidencia': None,
            'tipo_questao': []
        })
        self.nivel_recorrencia_pratica = data.get('nivel_recorrencia_pratica', 'MEDIA')
        self.dificuldade_compreensao = data.get('dificuldade_compreensao', 'INTERMEDIARIA')

        # Temporal
        self.vigencia_inicio = data.get('vigencia_inicio', '1988-10-05')
        self.vigencia_fim = data.get('vigencia_fim')

        # Fonte
        self.fonte_oficial = data.get('fonte_oficial', {})

        # Relacionamentos
        self.vinculo_superior = data.get('vinculo_superior')
        self.normas_relacionadas = data.get('normas_relacionadas', [])

    def gerar_hash(self) -> str:
        """Gera hash SHA-256 do texto normativo para validação."""
        return hashlib.sha256(self.texto_normativo.encode('utf-8')).hexdigest()

    def gerar_contexto_semantico(self) -> str:
        """Gera paráfrase sintética para contexto RAG."""
        return f"{self.instituto_juridico_principal} - {self.artigo} {self.nome_popular}: {self.texto_normativo[:150]}..."


# ============================================================
# PIPELINE DE INGESTÃO
# ============================================================

class PipelineIngestaoLeiSeca:
    """Pipeline completo de ingestão da lei seca."""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.stats = {
            'total_processadas': 0,
            'total_inseridas': 0,
            'total_atualizadas': 0,
            'total_puladas': 0,
            'total_erros': 0,
            'inicio': None,
            'fim': None,
            'batches_processados': 0
        }

    def carregar_dados_json(self, arquivo_path: str) -> List[Dict]:
        """Carrega dados de arquivo JSON."""
        logger.info(f"Carregando dados de {arquivo_path}")

        try:
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            logger.info(f"✓ {len(dados)} normas carregadas do arquivo")
            return dados

        except FileNotFoundError:
            logger.error(f"✗ Arquivo não encontrado: {arquivo_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"✗ Erro ao decodificar JSON: {e}")
            raise

    def validar_unidade(self, unidade: UnidadeNormativa) -> Tuple[bool, Optional[str]]:
        """Valida integridade da unidade normativa."""

        # Validação 1: Campos obrigatórios
        if not unidade.texto_normativo or len(unidade.texto_normativo) == 0:
            return False, "Texto normativo vazio"

        if not unidade.conceitos_chave or len(unidade.conceitos_chave) == 0:
            return False, "Conceitos-chave ausentes"

        # Validação 2: Tamanho razoável
        if len(unidade.texto_normativo) > 50000:
            return False, "Texto normativo muito longo (> 50k caracteres)"

        # Validação 3: Ramo válido
        ramos_validos = [
            'CONSTITUCIONAL', 'CIVIL', 'PENAL', 'PROCESSUAL_CIVIL',
            'PROCESSUAL_PENAL', 'TRABALHO', 'TRIBUTARIO', 'EMPRESARIAL',
            'CONSUMIDOR', 'ADMINISTRATIVO', 'AMBIENTAL'
        ]
        if unidade.ramo_direito not in ramos_validos:
            return False, f"Ramo inválido: {unidade.ramo_direito}"

        return True, None

    def norma_ja_existe(self, session, unidade: UnidadeNormativa) -> Optional[UUID]:
        """Verifica se norma já existe no banco (idempotência)."""

        result = session.execute(
            text("""
                SELECT id FROM norma_legal
                WHERE diploma_legal = :diploma
                  AND artigo = :artigo
                  AND COALESCE(paragrafo, '') = :paragrafo
                  AND COALESCE(inciso, '') = :inciso
                  AND COALESCE(alinea, '') = :alinea
            """),
            {
                'diploma': unidade.diploma_legal,
                'artigo': unidade.artigo,
                'paragrafo': unidade.paragrafo or '',
                'inciso': unidade.inciso or '',
                'alinea': unidade.alinea or ''
            }
        ).fetchone()

        return result[0] if result else None

    def inserir_norma(self, session, unidade: UnidadeNormativa) -> UUID:
        """Insere norma no banco de dados."""

        norma_id = uuid4()
        hash_texto = unidade.gerar_hash()
        contexto = unidade.gerar_contexto_semantico()

        # Palavras-chave para busca textual
        palavras_chave = self._extrair_palavras_chave(unidade)

        session.execute(
            text("""
                INSERT INTO norma_legal (
                    id, diploma_legal, nome_popular, artigo, paragrafo, inciso, alinea,
                    texto_normativo, ramo_direito, natureza_normativa, tipo_normativo,
                    instituto_juridico_principal, institutos_secundarios, conceitos_chave,
                    termos_tecnicos, incidencia_oab, nivel_recorrencia_pratica,
                    dificuldade_compreensao, vigencia_inicio, vigencia_fim,
                    fonte_oficial, normas_relacionadas, versao_atual,
                    palavras_chave_busca, contexto_semantico,
                    created_at, updated_at
                ) VALUES (
                    :id, :diploma_legal, :nome_popular, :artigo, :paragrafo, :inciso, :alinea,
                    :texto_normativo, :ramo_direito, :natureza_normativa, :tipo_normativo,
                    :instituto_juridico_principal, :institutos_secundarios, :conceitos_chave,
                    :termos_tecnicos, :incidencia_oab, :nivel_recorrencia_pratica,
                    :dificuldade_compreensao, :vigencia_inicio, :vigencia_fim,
                    :fonte_oficial, :normas_relacionadas, :versao_atual,
                    :palavras_chave_busca, :contexto_semantico,
                    :created_at, :updated_at
                )
            """),
            {
                'id': norma_id,
                'diploma_legal': unidade.diploma_legal,
                'nome_popular': unidade.nome_popular,
                'artigo': unidade.artigo,
                'paragrafo': unidade.paragrafo,
                'inciso': unidade.inciso,
                'alinea': unidade.alinea,
                'texto_normativo': unidade.texto_normativo,
                'ramo_direito': unidade.ramo_direito,
                'natureza_normativa': unidade.natureza_normativa,
                'tipo_normativo': unidade.tipo_normativo,
                'instituto_juridico_principal': unidade.instituto_juridico_principal,
                'institutos_secundarios': unidade.institutos_secundarios,
                'conceitos_chave': unidade.conceitos_chave,
                'termos_tecnicos': unidade.termos_tecnicos,
                'incidencia_oab': json.dumps(unidade.incidencia_oab),
                'nivel_recorrencia_pratica': unidade.nivel_recorrencia_pratica,
                'dificuldade_compreensao': unidade.dificuldade_compreensao,
                'vigencia_inicio': unidade.vigencia_inicio,
                'vigencia_fim': unidade.vigencia_fim,
                'fonte_oficial': json.dumps(unidade.fonte_oficial) if unidade.fonte_oficial else None,
                'normas_relacionadas': json.dumps(unidade.normas_relacionadas) if unidade.normas_relacionadas else None,
                'versao_atual': 1,
                'palavras_chave_busca': palavras_chave,
                'contexto_semantico': contexto,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
        )

        return norma_id

    def _extrair_palavras_chave(self, unidade: UnidadeNormativa) -> List[str]:
        """Extrai palavras-chave do texto normativo."""

        palavras = set()

        # Adicionar conceitos-chave
        for conceito in unidade.conceitos_chave:
            palavras.add(conceito.lower())

        # Adicionar termos técnicos
        for termo in unidade.termos_tecnicos:
            palavras.add(termo.lower())

        # Adicionar instituto
        palavras.add(unidade.instituto_juridico_principal.lower())

        # Adicionar identificação
        palavras.add(unidade.artigo.lower())
        palavras.add(unidade.nome_popular.lower())

        return list(palavras)

    def processar_batch(self, session, batch: List[UnidadeNormativa]) -> Dict:
        """Processa um lote de normas."""

        resultado = {
            'inseridas': 0,
            'puladas': 0,
            'erros': 0,
            'erros_detalhes': []
        }

        for unidade in batch:
            try:
                # Validar
                valido, erro = self.validar_unidade(unidade)
                if not valido:
                    logger.warning(f"⚠ Norma inválida ({unidade.artigo}): {erro}")
                    resultado['erros'] += 1
                    resultado['erros_detalhes'].append({
                        'artigo': unidade.artigo,
                        'erro': erro
                    })
                    continue

                # Verificar existência (idempotência)
                norma_existente = self.norma_ja_existe(session, unidade)
                if norma_existente:
                    logger.debug(f"○ Norma já existe: {unidade.artigo} (pulando)")
                    resultado['puladas'] += 1
                    continue

                # Inserir
                norma_id = self.inserir_norma(session, unidade)
                logger.info(f"✓ Norma inserida: {unidade.artigo} ({norma_id})")
                resultado['inseridas'] += 1

            except IntegrityError as e:
                logger.error(f"✗ Erro de integridade ao inserir {unidade.artigo}: {e}")
                resultado['erros'] += 1
                resultado['erros_detalhes'].append({
                    'artigo': unidade.artigo,
                    'erro': str(e)
                })
                session.rollback()

            except Exception as e:
                logger.error(f"✗ Erro inesperado ao inserir {unidade.artigo}: {e}")
                resultado['erros'] += 1
                resultado['erros_detalhes'].append({
                    'artigo': unidade.artigo,
                    'erro': str(e)
                })
                session.rollback()

        return resultado

    def executar(self, arquivo_json: str):
        """Executa pipeline completo de ingestão."""

        logger.info("=" * 80)
        logger.info("INICIANDO PIPELINE DE INGESTÃO DA LEI SECA")
        logger.info("=" * 80)

        self.stats['inicio'] = datetime.now(timezone.utc)

        try:
            # 1. Carregar dados
            dados = self.carregar_dados_json(arquivo_json)
            self.stats['total_processadas'] = len(dados)

            # 2. Converter para UnidadeNormativa
            unidades = [UnidadeNormativa(d) for d in dados]

            # 3. Processar em batches
            total_batches = (len(unidades) + self.batch_size - 1) // self.batch_size
            logger.info(f"Total de batches: {total_batches} (tamanho: {self.batch_size})")

            for i in range(0, len(unidades), self.batch_size):
                batch = unidades[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1

                logger.info(f"\n--- BATCH {batch_num}/{total_batches} ---")

                with get_db_session() as session:
                    try:
                        resultado = self.processar_batch(session, batch)

                        # Commit do batch
                        session.commit()

                        # Atualizar estatísticas
                        self.stats['total_inseridas'] += resultado['inseridas']
                        self.stats['total_puladas'] += resultado['puladas']
                        self.stats['total_erros'] += resultado['erros']
                        self.stats['batches_processados'] += 1

                        logger.info(f"Batch {batch_num}: {resultado['inseridas']} inseridas, "
                                  f"{resultado['puladas']} puladas, {resultado['erros']} erros")

                    except Exception as e:
                        logger.error(f"✗ ERRO NO BATCH {batch_num}: {e}")
                        session.rollback()
                        self.stats['total_erros'] += len(batch)

            self.stats['fim'] = datetime.now(timezone.utc)

            # 4. Relatório final
            self._gerar_relatorio()

        except Exception as e:
            logger.error(f"✗ ERRO FATAL NO PIPELINE: {e}")
            raise

    def _gerar_relatorio(self):
        """Gera relatório final de ingestão."""

        duracao = (self.stats['fim'] - self.stats['inicio']).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("RELATÓRIO FINAL DE INGESTÃO")
        logger.info("=" * 80)
        logger.info(f"Total processadas:  {self.stats['total_processadas']}")
        logger.info(f"Total inseridas:    {self.stats['total_inseridas']}")
        logger.info(f"Total puladas:      {self.stats['total_puladas']} (já existentes)")
        logger.info(f"Total erros:        {self.stats['total_erros']}")
        logger.info(f"Batches processados: {self.stats['batches_processados']}")
        logger.info(f"Duração:            {duracao:.2f} segundos")
        logger.info(f"Taxa:               {self.stats['total_inseridas'] / duracao:.2f} normas/segundo")
        logger.info("=" * 80)

        # Salvar relatório em arquivo
        self._salvar_relatorio_arquivo()

    def _salvar_relatorio_arquivo(self):
        """Salva relatório em arquivo."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = f"logs/relatorio_ingestao_lei_seca_{timestamp}.json"

        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'stats': {
                    'total_processadas': self.stats['total_processadas'],
                    'total_inseridas': self.stats['total_inseridas'],
                    'total_puladas': self.stats['total_puladas'],
                    'total_erros': self.stats['total_erros'],
                    'batches_processados': self.stats['batches_processados'],
                    'inicio': self.stats['inicio'].isoformat(),
                    'fim': self.stats['fim'].isoformat(),
                    'duracao_segundos': (self.stats['fim'] - self.stats['inicio']).total_seconds()
                }
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Relatório salvo em: {arquivo}")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Pipeline de ingestão da lei seca')
    parser.add_argument('arquivo', help='Arquivo JSON com normas')
    parser.add_argument('--batch-size', type=int, default=100, help='Tamanho do batch')

    args = parser.parse_args()

    # Criar diretório de logs se não existir
    Path('logs').mkdir(exist_ok=True)

    # Executar pipeline
    pipeline = PipelineIngestaoLeiSeca(batch_size=args.batch_size)
    pipeline.executar(args.arquivo)
