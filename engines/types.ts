/**
 * JURIS_IA_CORE_V1 - Definições de Tipos
 *
 * Sistema de tipos TypeScript para o motor de IA jurídica
 */

// ============================================================
// TIPOS DE EVENTOS DO ESTUDANTE
// ============================================================

export type EngineEventType =
  | 'erro'                        // Errou questão
  | 'erro_repetido'               // Errou mesmo conceito 3x
  | 'acerto'                      // Acertou questão
  | 'acerto_sequencial'           // Acertos consecutivos (5+)
  | 'tempo_excessivo'             // Demorou muito em questão
  | 'duvida'                      // Pediu explicação
  | 'inicio_sessao'               // Começou a estudar
  | 'fim_sessao'                  // Terminou sessão
  | 'bloco_completo'              // Completou módulo
  | 'simulado_iniciado'           // Começou simulado
  | 'simulado_concluido'          // Terminou simulado
  | 'revisao_devida'              // Ciclo de revisão ativado (1-24-7)
  | 'ansiedade'                   // Indicadores de ansiedade
  | 'frustração'                  // Sequência de erros
  | 'travamento'                  // Parou no meio
  | 'procrastinação'              // Não estuda há dias
  | 'baixa_confiança'             // Indicadores de baixa autoeficácia
  | 'queda_rendimento'            // Performance caindo
  | 'peca_iniciada'               // Começou peça (2ª fase)
  | 'peca_concluida'              // Terminou peça
  | 'erro_fatal_peca';            // Erro grave na peça

export interface EngineEvent {
  alunoId: string;
  tipo: EngineEventType;
  timestamp?: string;

  // Contexto do evento
  disciplina?: DisciplinaOAB;
  topico?: string;
  subtopico?: string;

  // Dados específicos
  dados?: {
    questaoId?: string;
    alternativaEscolhida?: string;
    alternativaCorreta?: string;
    tempoGasto?: number;          // segundos
    tentativa?: number;            // quantas vezes tentou
    dificuldade?: 'facil' | 'media' | 'dificil' | 'muito_dificil';
    anoProva?: number;
    bancaProva?: string;

    // Peça (2ª fase)
    pecaTipo?: TipoPeca;
    pecaArea?: AreaDireito;
    errosFatais?: string[];
    pontosPositivos?: string[];
    nota?: number;

    // Contexto adicional
    repetido?: boolean;
    estrutural?: boolean;         // erro conceitual grave
    pedidoAjuda?: boolean;
    conteudoDificil?: boolean;

    // Metadados
    [key: string]: any;
  };
}

// ============================================================
// DISCIPLINAS E ÁREAS
// ============================================================

export type DisciplinaOAB =
  | 'constitucional'
  | 'administrativo'
  | 'civil'
  | 'processual_civil'
  | 'penal'
  | 'processual_penal'
  | 'trabalho'
  | 'processual_trabalho'
  | 'tributario'
  | 'empresarial'
  | 'consumidor'
  | 'ambiental'
  | 'internacional'
  | 'eleitoral'
  | 'financeiro'
  | 'etica_oab'
  | 'filosofia_direito';

export type AreaDireito =
  | 'civil'
  | 'penal'
  | 'trabalho'
  | 'tributario'
  | 'empresarial'
  | 'constitucional'
  | 'administrativo';

export type TipoPeca =
  | 'petição_inicial'
  | 'contestação'
  | 'recurso_apelacao'
  | 'recurso_especial'
  | 'habeas_corpus'
  | 'mandado_segurança'
  | 'reclamacao_trabalhista'
  | 'parecer'
  | 'memorial'
  | 'contrarrazoes';

// ============================================================
// ESTADO DO ESTUDANTE
// ============================================================

export interface StudentState {
  alunoId: string;

  // Progresso por disciplina (0-100%)
  progressoDisciplinas: Record<DisciplinaOAB, number>;

  // Histórico recente
  errosRecentes: EngineEvent[];                  // últimos 20 erros
  acertosRecentes: EngineEvent[];                // últimos 20 acertos

  // Performance
  taxaAcerto: Record<DisciplinaOAB, number>;     // % acerto por disciplina
  tempoPorQuestao: Record<DisciplinaOAB, number>;// segundos médios

  // Nível emocional (0-100)
  nivelEmocional: {
    stress: number;
    motivacao: number;
    confianca: number;
  };

  // Erros estruturais (conceitos não dominados)
  errosEstruturais: string[];                    // "civil:prescrição", "penal:dolo_eventual"

  // Módulos acionados
  modulosAcionados: string[];                    // IDs dos módulos já ativados
  contagemModulos: Record<string, number>;       // quantas vezes cada módulo foi acionado

  // Ciclo de revisão
  revisoesAgendadas: RevisaoAgendada[];

  // Rotina
  rotinaSemanal: Record<string, number>;         // dia da semana → minutos estudados

  // Metadados
  atualizadoEm: string;
  sessoesHoje: number;
  streakAtual: number;                           // dias consecutivos estudando

  // OAB específico
  dataProvaOAB?: string;
  fase?: '1' | '2';
  area2fase?: AreaDireito;
  simuladosRealizados: number;
  mediaSimulados: number;
}

export interface RevisaoAgendada {
  id: string;
  disciplina: DisciplinaOAB;
  topico: string;
  ciclo: '1h' | '24h' | '7d';
  agendadoPara: string;                          // ISO timestamp
  concluida: boolean;
}

// ============================================================
// MÓDULOS DO ENGINE
// ============================================================

export type ModuleType =
  | 'MEMORY'                 // Técnicas de memorização
  | 'STRATEGY'               // Estratégias de resolução
  | 'EMOTIONAL'              // Controle emocional
  | 'ORGANIZATION'           // Organização de estudos
  | 'PRODUCTIVITY'           // Produtividade
  | 'HIGH_PERFORMANCE'       // Alta performance
  | 'OAB_STRATEGY'           // Estratégias específicas OAB
  | 'PECA_CONSTRUCTION'      // Construção de peças
  | 'JURISPRUDENCE'          // Uso de jurisprudência
  | 'INTERPRETATION';        // Interpretação jurídica

export interface EngineModule {
  id: string;                                    // M01, M02, etc
  nome: string;
  tipo: ModuleType;
  objetivo: string;

  // Gatilhos que ativam o módulo
  gatilhos: string[];

  // Algoritmo de atuação (passos)
  algoritmo: string[];

  // Ações de retorno
  acoesRetorno: string[];

  // Fonte/referência
  fonte: string;

  // Prioridade (1-10)
  prioridade: number;

  // Áreas alvo
  areasAlvo: DisciplinaOAB[] | ['all'];

  // Tags
  tags: string[];
}

// ============================================================
// AÇÕES DO ENGINE
// ============================================================

export type EngineActionType =
  | 'mostrar_mensagem'
  | 'gerar_drill'                                // Questões focadas
  | 'gerar_explicacao'                           // Explicação detalhada
  | 'sugerir_revisao'
  | 'agendar_revisao'
  | 'sugerir_pausa'
  | 'ajustar_rotina'
  | 'ativar_respiracao'
  | 'apresentar_questao_facil'
  | 'criar_flashcards'
  | 'mostrar_progresso'
  | 'reforçar_identidade'
  | 'simplificar_conteudo'
  | 'gerar_mapa_mental'
  | 'mostrar_jurisprudencia'
  | 'gerar_checklist_peca'
  | 'verificar_peca'
  | 'sugerir_fundamentacao';

export interface EngineAction {
  tipo: EngineActionType;
  titulo: string;
  mensagem: string;
  conteudo?: any;
  prioridade: 'baixa' | 'media' | 'alta';
}

// ============================================================
// GAMIFICAÇÃO
// ============================================================

export interface GamificationPayload {
  FP: number;                                    // Pontos de Foco
  moedas: number;
  missoesConcluidas: string[];
  badge?: string;
  descricao: string;
}

// ============================================================
// RESPOSTA DO ENGINE
// ============================================================

export interface EngineResponse {
  moduloId?: string;
  moduloNome?: string;
  moduloTipo?: ModuleType;
  moduloObjetivo?: string;

  acoes: EngineAction[];

  gamificacao?: GamificationPayload;

  novoEstado?: StudentState;

  razaoAtivacao?: string;
  scoreModulo?: number;

  processadoEm: string;
}

// ============================================================
// CONFIGURAÇÃO DO ENGINE
// ============================================================

export interface EngineConfig {
  pesoprioridade: number;                        // peso da prioridade do módulo
  pesoGatilho: number;                           // peso do match de gatilho
  penalidadeRepeticao: number;                   // penalidade por repetição
}

export const DEFAULT_ENGINE_CONFIG: EngineConfig = {
  pesoprioridade: 1.5,
  pesoGatilho: 3,
  penalidadeRepeticao: 0.5,
};

// ============================================================
// QUESTÕES E EXPLICAÇÕES
// ============================================================

export interface QuestaoOAB {
  id: string;
  enunciado: string;
  alternativas: Record<string, string>;          // A, B, C, D
  correta: string;                               // A, B, C, D

  // Metadados
  disciplina: DisciplinaOAB;
  topico: string;
  subtopico?: string;
  dificuldade: 'facil' | 'media' | 'dificil' | 'muito_dificil';

  // Origem
  anoProva?: number;
  faseProva: '1' | '2';
  banca?: string;

  // Pedagógico
  fundamentacao: string;                         // lei aplicável
  explicacao: string;
  explicacaoAlternativas: Record<string, string>;// por que cada alternativa está certa/errada
  pegadinhas?: string[];
  conceitosEnvolvidos: string[];

  // Relações
  questoesRelacionadas?: string[];
  artigosRelacionados?: string[];

  // Estatísticas
  taxaAcerto?: number;
  vezesResolvida?: number;
}

export interface ExplicacaoMultinivel {
  questaoId: string;
  alunoId: string;
  alternativaEscolhida: string;

  // Níveis de explicação
  nivel1_tecnica: string;                        // linguagem técnica
  nivel2_didatica: string;                       // explicação simples
  nivel3_analogia: string;                       // analogia intuitiva
  nivel4_exemplo: string;                        // exemplo prático

  // Análise de erro
  tipoErro?: 'conceitual' | 'leitura' | 'pressa' | 'desconhecimento';
  conceitosFalhos?: string[];
  sugestaoEstudo?: string;
}

// ============================================================
// PEÇAS (2ª FASE)
// ============================================================

export interface PecaOAB {
  id: string;
  tipo: TipoPeca;
  area: AreaDireito;

  // Estrutura
  requisitosFormais: string[];                   // endereçamento, qualificação, etc
  requisitosMateriais: string[];                 // fatos, fundamentos, pedido

  // Checklist
  checklist: ChecklistItem[];

  // Fundamentos
  fundamentosLegais: string[];                   // artigos aplicáveis
  fundamentosJurisprudenciais?: string[];        // súmulas, precedentes

  // Exemplos
  pecaModelo: string;
  pecasComentadas: string[];

  // Erros comuns
  errosFatais: string[];
  errosGraves: string[];
  errosLeves: string[];
}

export interface ChecklistItem {
  id: string;
  descricao: string;
  obrigatorio: boolean;
  peso: number;                                  // importância na nota
  verificacao: 'automatica' | 'manual';
}

export interface CorrecaoPeca {
  pecaId: string;
  alunoId: string;

  // Avaliação
  nota: number;                                  // 0-10
  aprovado: boolean;

  // Detalhamento
  pontosPositivos: string[];
  errosFatais: string[];
  errosGraves: string[];
  errosLeves: string[];

  // Por competência
  avaliacaoCompetencias: {
    forma: number;                               // 0-2
    conteudo: number;                            // 0-4
    fundamentacao: number;                       // 0-2
    tecnica: number;                             // 0-2
  };

  // Feedback
  feedbackGeral: string;
  sugestoesEspecificas: string[];

  // Revisão
  necessitaRevisao: boolean;
  topicosRevisar: string[];
}

// ============================================================
// LEI SECA ESTRUTURADA
// ============================================================

export interface ArtigoLei {
  id: string;
  lei: string;                                   // "CF/88", "CC/2002", "CP"
  artigo: string;                                // "5º", "121", "927"
  texto: string;

  // Estrutura
  caput?: string;
  incisos?: Record<string, string>;
  paragrafos?: Record<string, string>;

  // Pedagógico
  sintese: string;                               // resumo objetivo
  conceitosRelacionados: string[];
  excecoes?: string[];
  pegadinhasOAB: string[];

  // Incidência
  incidenciaOAB: {
    frequencia: 'alta' | 'media' | 'baixa';
    disciplinas: DisciplinaOAB[];
    tipoCobranca: string[];                      // "literal", "interpretação", "aplicação"
  };

  // Aplicação
  aplicacaoPratica: string;
  jurisprudenciaRelevante?: string[];

  // Relações
  artigosRelacionados: string[];
  questoesRelacionadas: string[];
}

// ============================================================
// ONTOLOGIA
// ============================================================

export interface ConceitoJuridico {
  id: string;
  nome: string;
  ramo: DisciplinaOAB;

  // Definições
  definicaoTecnica: string;
  explicacaoDidatica: string;

  // Relações
  conceitosPai: string[];                        // conceitos mais gerais
  conceitosFilho: string[];                      // conceitos mais específicos
  conceitosRelacionados: string[];
  distingueSe: Record<string, string>;           // outros conceitos que podem confundir

  // Incidência
  incidenciaOAB: {
    peso: 'alto' | 'medio' | 'baixo';
    disciplinas: DisciplinaOAB[];
    topicos: string[];
  };

  // Aplicação
  aplicacaoPratica: string;
  errosComuns: string[];

  // Pedagógico
  exemplos: string[];
  analogias?: string[];
  mapasMentais?: string[];
}

// ============================================================
// EXPORTS
// ============================================================

export {
  EngineEvent,
  EngineEventType,
  EngineResponse,
  StudentState,
  EngineModule,
  ModuleType,
  EngineAction,
  EngineActionType,
  GamificationPayload,
  EngineConfig,
  DEFAULT_ENGINE_CONFIG,
};
