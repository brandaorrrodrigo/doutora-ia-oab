#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PIPELINE DE INGESTÃO DE QUESTÕES OAB - ETAPA 9.2
================================================================================

Script de ingestão em lote de questões do Exame da OAB com:
- Isolamento do gabarito em tabela protegida
- Classificação de erros por alternativa
- Associação com normas e conceitos
- Indexação para performance
- Log detalhado por lote
- Garantia de idempotência

Autor: JURIS IA CORE V1
Data: 2025-12-17
================================================================================
"""

import json
import sys
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from decimal import Decimal

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from database.connection import DatabaseConnection


# ================================================================================
# CONFIGURAÇÃO DE LOGGING
# ================================================================================

def configurar_logging():
    """Configura logging para arquivo e console."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"ingestao_questoes_oab_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return str(log_file)


# ================================================================================
# MODELOS DE DADOS
# ================================================================================

class Alternativa:
    """Representa uma alternativa de questão."""

    def __init__(self, letra: str, texto: str, tipo_erro: Optional[str] = None):
        self.letra = letra
        self.texto = texto
        self.tipo_erro = tipo_erro  # None se for a alternativa correta

    def validar(self) -> Tuple[bool, Optional[str]]:
        """Valida a alternativa."""
        if not self.letra or len(self.letra) != 1:
            return False, "Letra da alternativa inválida"

        if not self.texto or len(self.texto.strip()) < 10:
            return False, "Texto da alternativa muito curto"

        if len(self.texto) > 2000:
            return False, "Texto da alternativa excede limite de 2000 caracteres"

        # Tipos de erro válidos (conforme ETAPA 3.3)
        tipos_erro_validos = [
            "conceitual",
            "normativo",
            "interpretacao",
            "estrategico",
            "leitura",
            "confusao_institutos"
        ]

        if self.tipo_erro is not None and self.tipo_erro not in tipos_erro_validos:
            return False, f"Tipo de erro inválido: {self.tipo_erro}"

        return True, None


class QuestaoOAB:
    """Representa uma questão OAB para ingestão."""

    def __init__(self, data: Dict):
        self.numero_questao = data['numero_questao']
        self.exame = data['exame']
        self.fase = data['fase']
        self.area = data['area']
        self.enunciado = data['enunciado']

        # Alternativas
        self.alternativas = [
            Alternativa(alt['letra'], alt['texto'], alt.get('tipo_erro'))
            for alt in data['alternativas']
        ]

        # Gabarito (isolado)
        self.gabarito = data['gabarito']

        # Associações
        self.normas_associadas = data.get('normas_associadas', [])
        self.conceitos_associados = data.get('conceitos_associados', [])

        # Metadata avaliativa (conforme ETAPA 3.2)
        self.dificuldade_real = Decimal(str(data.get('dificuldade_real', 0.5)))
        self.tempo_medio_observado = data.get('tempo_medio_observado', 120)  # segundos
        self.frequencia_historica = Decimal(str(data.get('frequencia_historica', 0.0)))

        # Metadados adicionais
        self.data_aplicacao = data.get('data_aplicacao')
        self.regiao = data.get('regiao')

    def gerar_hash(self) -> str:
        """Gera hash SHA-256 do enunciado para validação de integridade."""
        return hashlib.sha256(self.enunciado.encode('utf-8')).hexdigest()

    def validar(self) -> Tuple[bool, Optional[str]]:
        """Valida a questão completa."""

        # Validar número da questão
        if not self.numero_questao or len(self.numero_questao) < 5:
            return False, "Número da questão inválido"

        # Validar enunciado
        if not self.enunciado or len(self.enunciado.strip()) < 20:
            return False, "Enunciado muito curto"

        if len(self.enunciado) > 5000:
            return False, "Enunciado excede limite de 5000 caracteres"

        # Validar alternativas
        if len(self.alternativas) < 2:
            return False, "Questão deve ter pelo menos 2 alternativas"

        if len(self.alternativas) > 5:
            return False, "Questão não pode ter mais de 5 alternativas"

        # Validar cada alternativa
        for alt in self.alternativas:
            valido, erro = alt.validar()
            if not valido:
                return False, f"Alternativa {alt.letra}: {erro}"

        # Validar gabarito
        if not self.gabarito or len(self.gabarito) != 1:
            return False, "Gabarito inválido"

        letras_alternativas = [alt.letra for alt in self.alternativas]
        if self.gabarito not in letras_alternativas:
            return False, f"Gabarito '{self.gabarito}' não corresponde a nenhuma alternativa"

        # Verificar que gabarito não tem tipo_erro
        for alt in self.alternativas:
            if alt.letra == self.gabarito and alt.tipo_erro is not None:
                return False, f"Alternativa correta ({self.gabarito}) não pode ter tipo_erro"

        # Verificar que alternativas incorretas têm tipo_erro
        for alt in self.alternativas:
            if alt.letra != self.gabarito and alt.tipo_erro is None:
                return False, f"Alternativa incorreta ({alt.letra}) deve ter tipo_erro"

        # Validar área
        areas_validas = [
            "Direito Constitucional",
            "Direito Administrativo",
            "Direito Civil",
            "Direito Processual Civil",
            "Direito Penal",
            "Direito Processual Penal",
            "Direito Empresarial",
            "Direito do Trabalho",
            "Direito Tributário",
            "Direitos Humanos",
            "Ética e Estatuto da OAB",
            "Direito do Consumidor",
            "Direito Ambiental",
            "Filosofia do Direito"
        ]

        if self.area not in areas_validas:
            return False, f"Área inválida: {self.area}"

        # Validar fase
        if self.fase not in ["1ª Fase", "2ª Fase"]:
            return False, f"Fase inválida: {self.fase}"

        # Validar dificuldade_real (0-1)
        if not (0 <= self.dificuldade_real <= 1):
            return False, "dificuldade_real deve estar entre 0 e 1"

        # Validar tempo_medio_observado (30-600 segundos)
        if not (30 <= self.tempo_medio_observado <= 600):
            return False, "tempo_medio_observado deve estar entre 30 e 600 segundos"

        # Validar frequencia_historica (0-1)
        if not (0 <= self.frequencia_historica <= 1):
            return False, "frequencia_historica deve estar entre 0 e 1"

        return True, None


# ================================================================================
# PIPELINE DE INGESTÃO
# ================================================================================

class PipelineIngestaoQuestoesOAB:
    """Pipeline de ingestão em lote de questões OAB."""

    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self.db = DatabaseConnection()
        self.logger = logging.getLogger(__name__)

    def carregar_dados_json(self, arquivo_json: str) -> List[QuestaoOAB]:
        """Carrega questões de arquivo JSON."""
        self.logger.info(f"Carregando dados de {arquivo_json}")

        try:
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            if isinstance(dados, dict) and 'questoes' in dados:
                dados = dados['questoes']

            questoes = [QuestaoOAB(q) for q in dados]
            self.logger.info(f"Total de {len(questoes)} questões carregadas")

            return questoes

        except FileNotFoundError:
            self.logger.error(f"Arquivo não encontrado: {arquivo_json}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao parsear JSON: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados: {e}")
            raise

    def validar_questao(self, questao: QuestaoOAB) -> Tuple[bool, Optional[str]]:
        """Valida uma questão antes da ingestão."""
        return questao.validar()

    def questao_ja_existe(self, session, questao: QuestaoOAB) -> Optional[UUID]:
        """Verifica se questão já existe no banco (idempotência)."""
        result = session.execute(
            text("""
                SELECT id FROM questao_oab
                WHERE numero_questao = :numero
            """),
            {"numero": questao.numero_questao}
        ).fetchone()

        return result[0] if result else None

    def inserir_questao(self, session, questao: QuestaoOAB) -> UUID:
        """Insere questão na tabela questao_oab (SEM gabarito)."""
        questao_id = uuid4()

        # Gerar hash do enunciado
        hash_enunciado = questao.gerar_hash()

        # Montar alternativas como JSONB
        alternativas_json = json.dumps([
            {
                "letra": alt.letra,
                "texto": alt.texto
            }
            for alt in questao.alternativas
        ])

        session.execute(
            text("""
                INSERT INTO questao_oab (
                    id,
                    numero_questao,
                    exame,
                    fase,
                    area,
                    enunciado,
                    alternativas,
                    dificuldade_real,
                    tempo_medio_observado,
                    frequencia_historica,
                    hash_enunciado,
                    data_aplicacao,
                    regiao,
                    created_at
                ) VALUES (
                    :id,
                    :numero_questao,
                    :exame,
                    :fase,
                    :area,
                    :enunciado,
                    :alternativas::jsonb,
                    :dificuldade_real,
                    :tempo_medio_observado,
                    :frequencia_historica,
                    :hash_enunciado,
                    :data_aplicacao,
                    :regiao,
                    NOW()
                )
            """),
            {
                "id": questao_id,
                "numero_questao": questao.numero_questao,
                "exame": questao.exame,
                "fase": questao.fase,
                "area": questao.area,
                "enunciado": questao.enunciado,
                "alternativas": alternativas_json,
                "dificuldade_real": float(questao.dificuldade_real),
                "tempo_medio_observado": questao.tempo_medio_observado,
                "frequencia_historica": float(questao.frequencia_historica),
                "hash_enunciado": hash_enunciado,
                "data_aplicacao": questao.data_aplicacao,
                "regiao": questao.regiao
            }
        )

        self.logger.debug(f"Questão {questao.numero_questao} inserida com ID {questao_id}")
        return questao_id

    def inserir_gabarito(self, session, questao_id: UUID, gabarito: str):
        """Insere gabarito em tabela isolada e protegida."""
        session.execute(
            text("""
                INSERT INTO gabarito_questao (
                    id,
                    questao_id,
                    alternativa_correta,
                    created_at
                ) VALUES (
                    :id,
                    :questao_id,
                    :alternativa_correta,
                    NOW()
                )
            """),
            {
                "id": uuid4(),
                "questao_id": questao_id,
                "alternativa_correta": gabarito
            }
        )

        self.logger.debug(f"Gabarito '{gabarito}' inserido para questão {questao_id}")

    def inserir_erros_alternativas(self, session, questao_id: UUID, questao: QuestaoOAB):
        """Insere classificação de erros para alternativas incorretas."""
        for alt in questao.alternativas:
            # Apenas alternativas incorretas têm tipo_erro
            if alt.letra != questao.gabarito and alt.tipo_erro:
                session.execute(
                    text("""
                        INSERT INTO alternativa_erro (
                            id,
                            questao_id,
                            alternativa_letra,
                            tipo_erro,
                            created_at
                        ) VALUES (
                            :id,
                            :questao_id,
                            :alternativa_letra,
                            :tipo_erro,
                            NOW()
                        )
                    """),
                    {
                        "id": uuid4(),
                        "questao_id": questao_id,
                        "alternativa_letra": alt.letra,
                        "tipo_erro": alt.tipo_erro
                    }
                )

        self.logger.debug(f"Erros de alternativas inseridos para questão {questao_id}")

    def associar_normas(self, session, questao_id: UUID, codigos_normas: List[str]):
        """Associa questão com normas legais."""
        for codigo_norma in codigos_normas:
            # Buscar ID da norma pelo código
            result = session.execute(
                text("""
                    SELECT id FROM norma_legal
                    WHERE codigo_identificador = :codigo
                """),
                {"codigo": codigo_norma}
            ).fetchone()

            if result:
                norma_id = result[0]
                session.execute(
                    text("""
                        INSERT INTO questao_norma_associacao (
                            id,
                            questao_id,
                            norma_id,
                            created_at
                        ) VALUES (
                            :id,
                            :questao_id,
                            :norma_id,
                            NOW()
                        )
                    """),
                    {
                        "id": uuid4(),
                        "questao_id": questao_id,
                        "norma_id": norma_id
                    }
                )
                self.logger.debug(f"Norma {codigo_norma} associada à questão {questao_id}")
            else:
                self.logger.warning(f"Norma {codigo_norma} não encontrada no banco")

    def associar_conceitos(self, session, questao_id: UUID, codigos_conceitos: List[str]):
        """Associa questão com conceitos jurídicos."""
        for codigo_conceito in codigos_conceitos:
            # Buscar ID do conceito pelo código
            result = session.execute(
                text("""
                    SELECT id FROM conceito_juridico
                    WHERE codigo_identificador = :codigo
                """),
                {"codigo": codigo_conceito}
            ).fetchone()

            if result:
                conceito_id = result[0]
                session.execute(
                    text("""
                        INSERT INTO questao_conceito_associacao (
                            id,
                            questao_id,
                            conceito_id,
                            created_at
                        ) VALUES (
                            :id,
                            :questao_id,
                            :conceito_id,
                            NOW()
                        )
                    """),
                    {
                        "id": uuid4(),
                        "questao_id": questao_id,
                        "conceito_id": conceito_id
                    }
                )
                self.logger.debug(f"Conceito {codigo_conceito} associado à questão {questao_id}")
            else:
                self.logger.warning(f"Conceito {codigo_conceito} não encontrado no banco")

    def processar_batch(self, session, batch: List[QuestaoOAB]) -> Dict:
        """Processa um lote de questões."""
        resultado = {
            "inseridas": 0,
            "puladas": 0,
            "erros": 0,
            "detalhes_erros": []
        }

        for questao in batch:
            try:
                # Validar questão
                valido, erro = self.validar_questao(questao)
                if not valido:
                    self.logger.warning(
                        f"Questão {questao.numero_questao} inválida: {erro}"
                    )
                    resultado["erros"] += 1
                    resultado["detalhes_erros"].append({
                        "questao": questao.numero_questao,
                        "erro": erro
                    })
                    continue

                # Verificar se já existe (idempotência)
                if self.questao_ja_existe(session, questao):
                    self.logger.info(
                        f"Questão {questao.numero_questao} já existe - pulando"
                    )
                    resultado["puladas"] += 1
                    continue

                # Inserir questão (sem gabarito)
                questao_id = self.inserir_questao(session, questao)

                # Inserir gabarito (isolado)
                self.inserir_gabarito(session, questao_id, questao.gabarito)

                # Inserir erros de alternativas
                self.inserir_erros_alternativas(session, questao_id, questao)

                # Associar com normas
                if questao.normas_associadas:
                    self.associar_normas(session, questao_id, questao.normas_associadas)

                # Associar com conceitos
                if questao.conceitos_associados:
                    self.associar_conceitos(session, questao_id, questao.conceitos_associados)

                resultado["inseridas"] += 1
                self.logger.info(f"Questão {questao.numero_questao} processada com sucesso")

            except IntegrityError as e:
                self.logger.error(
                    f"Erro de integridade ao processar {questao.numero_questao}: {e}"
                )
                resultado["erros"] += 1
                resultado["detalhes_erros"].append({
                    "questao": questao.numero_questao,
                    "erro": str(e)
                })
                session.rollback()
                raise  # Re-raise para forçar rollback do batch

            except Exception as e:
                self.logger.error(
                    f"Erro ao processar {questao.numero_questao}: {e}"
                )
                resultado["erros"] += 1
                resultado["detalhes_erros"].append({
                    "questao": questao.numero_questao,
                    "erro": str(e)
                })

        return resultado

    def executar(self, arquivo_json: str) -> Dict:
        """Executa o pipeline completo de ingestão."""
        inicio = datetime.now()
        self.logger.info("=" * 80)
        self.logger.info("INICIANDO PIPELINE DE INGESTÃO DE QUESTÕES OAB")
        self.logger.info("=" * 80)

        try:
            # Carregar dados
            questoes = self.carregar_dados_json(arquivo_json)
            total_questoes = len(questoes)

            # Dividir em batches
            batches = [
                questoes[i:i + self.batch_size]
                for i in range(0, total_questoes, self.batch_size)
            ]

            self.logger.info(f"Total de {total_questoes} questões em {len(batches)} batches")

            # Processar batches
            resultado_total = {
                "inseridas": 0,
                "puladas": 0,
                "erros": 0,
                "detalhes_erros": []
            }

            with self.db.get_session() as session:
                for idx, batch in enumerate(batches, 1):
                    self.logger.info(f"\n--- Processando batch {idx}/{len(batches)} ---")

                    try:
                        resultado_batch = self.processar_batch(session, batch)
                        session.commit()

                        # Acumular resultados
                        resultado_total["inseridas"] += resultado_batch["inseridas"]
                        resultado_total["puladas"] += resultado_batch["puladas"]
                        resultado_total["erros"] += resultado_batch["erros"]
                        resultado_total["detalhes_erros"].extend(
                            resultado_batch["detalhes_erros"]
                        )

                        self.logger.info(
                            f"Batch {idx}: {resultado_batch['inseridas']} inseridas, "
                            f"{resultado_batch['puladas']} puladas, "
                            f"{resultado_batch['erros']} erros"
                        )

                    except Exception as e:
                        self.logger.error(f"Erro no batch {idx}: {e}")
                        session.rollback()
                        # Continua com próximo batch

            # Gerar relatório final
            fim = datetime.now()
            duracao = (fim - inicio).total_seconds()

            relatorio = self._gerar_relatorio(
                resultado_total,
                total_questoes,
                duracao
            )

            self.logger.info("\n" + "=" * 80)
            self.logger.info("RELATÓRIO FINAL")
            self.logger.info("=" * 80)
            self.logger.info(f"Total processadas: {total_questoes}")
            self.logger.info(f"Inseridas: {resultado_total['inseridas']}")
            self.logger.info(f"Puladas: {resultado_total['puladas']}")
            self.logger.info(f"Erros: {resultado_total['erros']}")
            self.logger.info(f"Duração: {duracao:.2f}s")
            self.logger.info(f"Performance: {relatorio['questoes_por_segundo']:.2f} questões/s")
            self.logger.info("=" * 80)

            return relatorio

        except Exception as e:
            self.logger.error(f"Erro crítico no pipeline: {e}")
            raise

    def _gerar_relatorio(
        self,
        resultado: Dict,
        total: int,
        duracao: float
    ) -> Dict:
        """Gera relatório final da ingestão."""
        questoes_por_segundo = resultado["inseridas"] / duracao if duracao > 0 else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "total_questoes": total,
            "inseridas": resultado["inseridas"],
            "puladas": resultado["puladas"],
            "erros": resultado["erros"],
            "duracao_segundos": duracao,
            "questoes_por_segundo": questoes_por_segundo,
            "detalhes_erros": resultado["detalhes_erros"]
        }


# ================================================================================
# INTERFACE DE LINHA DE COMANDO
# ================================================================================

def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Pipeline de ingestão de questões OAB em lote'
    )
    parser.add_argument(
        'arquivo_json',
        help='Arquivo JSON com questões OAB'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Tamanho do batch de processamento (padrão: 50)'
    )
    parser.add_argument(
        '--output',
        help='Arquivo de saída para relatório JSON (opcional)'
    )

    args = parser.parse_args()

    # Configurar logging
    log_file = configurar_logging()
    print(f"Log salvo em: {log_file}")

    # Executar pipeline
    pipeline = PipelineIngestaoQuestoesOAB(batch_size=args.batch_size)

    try:
        relatorio = pipeline.executar(args.arquivo_json)

        # Salvar relatório JSON se especificado
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False)
            print(f"\nRelatório salvo em: {args.output}")

        print("\n✓ Ingestão concluída com sucesso!")
        return 0

    except Exception as e:
        print(f"\n✗ Erro na ingestão: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
