/**
 * JURIS_IA_CORE_V1 - Base de Módulos Jurídicos
 *
 * Módulos especializados para formação jurídica e aprovação OAB
 * Inspirado no ENEM-IA mas adaptado para o contexto jurídico
 */

import { EngineModule, ModuleType } from './types';

// ============================================================
// MÓDULOS 01-10: MEMÓRIA E FIXAÇÃO JURÍDICA
// ============================================================

const J01: EngineModule = {
  id: 'J01',
  nome: 'Ciclo 1-24-7 Jurídico',
  tipo: 'MEMORY',
  objetivo: 'Fixar conceitos jurídicos com revisão espaçada científica adaptada ao Direito.',
  gatilhos: ['bloco_completo', 'revisao_devida', 'acerto'],
  algoritmo: [
    'Ciclo 1h: questão rápida sobre conceito estudado',
    'Ciclo 24h: 3 questões sobre tema com variações',
    'Ciclo 7d: 5 questões mesclando o tema com outros',
    'Se erro em qualquer ciclo, reinicia do ciclo 1h',
    'Rastrear com timestamps e ajustar intervalos'
  ],
  acoesRetorno: ['gerar_drill', 'agendar_revisao'],
  fonte: 'Técnicas de Memorização + Curva de Esquecimento Ebbinghaus',
  prioridade: 9,
  areasAlvo: ['all'],
  tags: ['revisão', 'memória', 'espaçada', 'fixação']
};

const J02: EngineModule = {
  id: 'J02',
  nome: 'Lei Seca Estruturada',
  tipo: 'MEMORY',
  objetivo: 'Memorizar artigos de lei através de estruturação lógica, não decoreba.',
  gatilhos: ['conteudoDificil', 'erro_repetido', 'duvida'],
  algoritmo: [
    'Identificar artigos essenciais do tema',
    'Estruturar artigo: caput → incisos → parágrafos → exceções',
    'Criar mnemônico para ordem dos incisos',
    'Ligar artigo a caso concreto',
    'Gerar questão que cobre pegadinha típica OAB'
  ],
  acoesRetorno: ['gerar_explicacao', 'gerar_drill', 'criar_flashcards'],
  fonte: 'Metodologia de Estudo de Lei Seca',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['lei_seca', 'memorização', 'artigos', 'estrutura']
};

const J03: EngineModule = {
  id: 'J03',
  nome: 'Mapa de Institutos Jurídicos',
  tipo: 'MEMORY',
  objetivo: 'Criar mapa mental de institutos e suas relações para fixação sistêmica.',
  gatilhos: ['bloco_completo', 'duvida', 'erro_repetido'],
  algoritmo: [
    'Identificar instituto central (ex: prescrição)',
    'Mapear conceitos relacionados (decadência, prazos, suspensão, interrupção)',
    'Estabelecer diferenças críticas',
    'Criar perguntas que explorem as distinções',
    'Testar compreensão com caso prático'
  ],
  acoesRetorno: ['gerar_mapa_mental', 'gerar_drill', 'mostrar_progresso'],
  fonte: 'Mapas Mentais Jurídicos',
  prioridade: 7,
  areasAlvo: ['all'],
  tags: ['mapa_mental', 'institutos', 'relações', 'sistêmico']
};

const J04: EngineModule = {
  id: 'J04',
  nome: 'Súmulas e Precedentes Vinculantes',
  tipo: 'MEMORY',
  objetivo: 'Memorizar súmulas e precedentes essenciais com aplicação prática.',
  gatilhos: ['duvida', 'conteudoDificil', 'bloco_completo'],
  algoritmo: [
    'Identificar súmulas mais cobradas na OAB',
    'Explicar contexto histórico da súmula',
    'Mostrar aplicação em caso concreto',
    'Criar questão OAB típica sobre a súmula',
    'Agendar revisão em 7 dias'
  ],
  acoesRetorno: ['mostrar_jurisprudencia', 'gerar_drill', 'agendar_revisao'],
  fonte: 'Jurisprudência STF e STJ',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['súmulas', 'precedentes', 'jurisprudência', 'aplicação']
};

const J05: EngineModule = {
  id: 'J05',
  nome: 'Mnemônicos Jurídicos',
  tipo: 'MEMORY',
  objetivo: 'Criar mnemônicos eficazes para listas, prazos e sequências jurídicas.',
  gatilhos: ['conteudoDificil', 'erro_repetido'],
  algoritmo: [
    'Identificar lista ou sequência difícil (ex: legitimados ADI)',
    'Criar mnemônico usando iniciais ou frase memorável',
    'Testar retenção imediata',
    'Aplicar em questão prática',
    'Revisar em 24h'
  ],
  acoesRetorno: ['gerar_explicacao', 'criar_flashcards', 'gerar_drill'],
  fonte: 'Técnicas Mnemônicas Aplicadas ao Direito',
  prioridade: 6,
  areasAlvo: ['all'],
  tags: ['mnemônico', 'memorização', 'listas', 'sequências']
};

const J06: EngineModule = {
  id: 'J06',
  nome: 'Casos Concretos para Fixação',
  tipo: 'MEMORY',
  objetivo: 'Transformar teoria abstrata em casos concretos memoráveis.',
  gatilhos: ['conteudoDificil', 'erro', 'duvida'],
  algoritmo: [
    'Identificar conceito abstrato difícil',
    'Criar caso concreto simples e memorável',
    'Aplicar conceito ao caso passo a passo',
    'Variar caso para explorar nuances',
    'Testar com questão OAB similar'
  ],
  acoesRetorno: ['gerar_explicacao', 'gerar_drill'],
  fonte: 'Método do Caso Concreto',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['caso_concreto', 'aplicação', 'prática', 'fixação']
};

const J07: EngineModule = {
  id: 'J07',
  nome: 'Flashcards Jurídicos Inteligentes',
  tipo: 'MEMORY',
  objetivo: 'Criar flashcards personalizados com base em erros e lacunas.',
  gatilhos: ['erro_repetido', 'fim_sessao', 'revisao_devida'],
  algoritmo: [
    'Transformar erros em flashcards (frente: pergunta, verso: resposta + fundamento)',
    'Agrupar por disciplina e dificuldade',
    'Aplicar revisão espaçada (1-24-7)',
    'Remover quando domínio atingido (3 acertos consecutivos)',
    'Estatística de retenção por flashcard'
  ],
  acoesRetorno: ['criar_flashcards', 'agendar_revisao'],
  fonte: 'Anki e Spaced Repetition',
  prioridade: 7,
  areasAlvo: ['all'],
  tags: ['flashcards', 'revisão', 'personalizado', 'erros']
};

const J08: EngineModule = {
  id: 'J08',
  nome: 'Técnica Feynman Jurídica',
  tipo: 'MEMORY',
  objetivo: 'Garantir compreensão profunda, não memorização superficial.',
  gatilhos: ['bloco_completo', 'conteudoDificil', 'erro_repetido'],
  algoritmo: [
    'Pedir: Explique [conceito] como se fosse para leigo',
    'Identificar lacunas na explicação do aluno',
    'Gerar explicação simplificada modelo',
    'Pedir novamente com analogia do cotidiano',
    'Confirmar compreensão com questão prática'
  ],
  acoesRetorno: ['gerar_explicacao', 'simplificar_conteudo', 'gerar_drill'],
  fonte: 'Técnica Feynman Adaptada ao Direito',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['Feynman', 'compreensão', 'explicação', 'profundidade']
};

const J09: EngineModule = {
  id: 'J09',
  nome: 'Árvore de Decisão Jurídica',
  tipo: 'MEMORY',
  objetivo: 'Organizar raciocínio jurídico em árvores de decisão lógicas.',
  gatilhos: ['conteudoDificil', 'erro_repetido', 'duvida'],
  algoritmo: [
    'Identificar ponto de decisão (ex: competência absoluta ou relativa?)',
    'Criar árvore: pergunta → sim/não → próxima pergunta',
    'Treinar navegação na árvore com casos',
    'Internalizar lógica progressivamente',
    'Aplicar em questão OAB'
  ],
  acoesRetorno: ['gerar_mapa_mental', 'gerar_drill'],
  fonte: 'Lógica Jurídica e Árvores de Decisão',
  prioridade: 7,
  areasAlvo: ['all'],
  tags: ['árvore', 'decisão', 'lógica', 'raciocínio']
};

const J10: EngineModule = {
  id: 'J10',
  nome: 'Associação Jurisprudência + Lei',
  tipo: 'MEMORY',
  objetivo: 'Ligar artigos de lei a súmulas e precedentes para fixação robusta.',
  gatilhos: ['bloco_completo', 'conteudoDificil'],
  algoritmo: [
    'Identificar artigo de lei importante',
    'Buscar súmula ou precedente relacionado',
    'Explicar como jurisprudência interpreta/modula a lei',
    'Criar questão que exige ambos (lei + súmula)',
    'Agendar revisão em 7 dias'
  ],
  acoesRetorno: ['mostrar_jurisprudencia', 'gerar_drill', 'agendar_revisao'],
  fonte: 'Integração Lei + Jurisprudência',
  prioridade: 7,
  areasAlvo: ['all'],
  tags: ['lei', 'jurisprudência', 'integração', 'aplicação']
};

// ============================================================
// MÓDULOS 11-20: ESTRATÉGIA DE RESOLUÇÃO OAB
// ============================================================

const J11: EngineModule = {
  id: 'J11',
  nome: 'Ataque pelas Alternativas',
  tipo: 'OAB_STRATEGY',
  objetivo: 'Ensinar a eliminar alternativas erradas antes de confirmar a certa.',
  gatilhos: ['tempo_excessivo', 'erro', 'duvida'],
  algoritmo: [
    'Ler alternativas ANTES do enunciado completo',
    'Eliminar 2 alternativas claramente erradas',
    'Comparar as 2 restantes com enunciado',
    'Identificar palavras absolutas (sempre, nunca, exclusivamente) como suspeitas',
    'Treinar justificativa de eliminação'
  ],
  acoesRetorno: ['gerar_explicacao', 'gerar_drill'],
  fonte: 'Estratégias de Múltipla Escolha',
  prioridade: 9,
  areasAlvo: ['all'],
  tags: ['alternativas', 'eliminação', 'estratégia', 'eficiência']
};

const J12: EngineModule = {
  id: 'J12',
  nome: 'Palavras-Chave do Enunciado',
  tipo: 'OAB_STRATEGY',
  objetivo: 'Identificar palavras-chave que direcionam à resposta correta.',
  gatilhos: ['tempo_excessivo', 'erro', 'conteudoDificil'],
  algoritmo: [
    'Destacar verbos de comando (analise, compare, identifique)',
    'Identificar qualificadores (exclusivamente, preferencialmente)',
    'Localizar negações (NÃO, EXCETO, INCORRETO)',
    'Focar no que realmente está sendo perguntado',
    'Treinar com 10 questões focando só em palavras-chave'
  ],
  acoesRetorno: ['gerar_explicacao', 'gerar_drill'],
  fonte: 'Análise Linguística de Questões',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['palavras-chave', 'enunciado', 'foco', 'leitura']
};

const J13: EngineModule = {
  id: 'J13',
  nome: 'Pegadinhas Clássicas OAB',
  tipo: 'OAB_STRATEGY',
  objetivo: 'Reconhecer e neutralizar pegadinhas recorrentes da banca.',
  gatilhos: ['erro_repetido', 'conteudoDificil'],
  algoritmo: [
    'Catalogar pegadinhas por tipo (inversão, exceção, prazo, legitimidade)',
    'Mostrar exemplos de cada tipo',
    'Treinar reconhecimento em questões reais',
    'Criar alerta mental para cada tipo',
    'Estatística: quais pegadinhas o aluno mais cai'
  ],
  acoesRetorno: ['gerar_explicacao', 'gerar_drill'],
  fonte: 'Análise de Provas OAB 2010-2024',
  prioridade: 9,
  areasAlvo: ['all'],
  tags: ['pegadinhas', 'OAB', 'padrões', 'armadilhas']
};

const J14: EngineModule = {
  id: 'J14',
  nome: 'Gestão de Tempo na Prova',
  tipo: 'OAB_STRATEGY',
  objetivo: 'Otimizar tempo: 3min/questão, priorizar fáceis, não travar.',
  gatilhos: ['tempo_excessivo', 'simulado_iniciado', 'ansiedade'],
  algoritmo: [
    'Definir meta: 3min por questão (80 questões em 4h = 3min)',
    'Treinar identificação de questões fáceis (resolver primeiro)',
    'Protocolo de travamento: mais de 4min → marcar para revisar e pular',
    'Últimos 30min: revisar marcadas + preencher chutes inteligentes',
    'Simular com cronômetro'
  ],
  acoesRetorno: ['mostrar_mensagem', 'gerar_drill', 'sugerir_pausa'],
  fonte: 'Gestão de Tempo em Provas',
  prioridade: 9,
  areasAlvo: ['all'],
  tags: ['tempo', 'prova', 'gestão', 'estratégia']
};

const J15: EngineModule = {
  id: 'J15',
  nome: 'Chute Inteligente',
  tipo: 'OAB_STRATEGY',
  objetivo: 'Maximizar chances quando não souber: eliminar + padrões estatísticos.',
  gatilhos: ['duvida', 'tempo_excessivo'],
  algoritmo: [
    'Eliminar alternativas absurdas',
    'Se restarem 2-3: usar padrões (alternativa do meio, mais longa, mais específica)',
    'Evitar absolutismos (sempre, nunca) no chute',
    'Marcar para revisar se sobrar tempo',
    'Nunca deixar em branco'
  ],
  acoesRetorno: ['mostrar_mensagem', 'gerar_explicacao'],
  fonte: 'Estratégias de Chute',
  prioridade: 6,
  areasAlvo: ['all'],
  tags: ['chute', 'eliminação', 'estatística', 'padrões']
};

const J16: EngineModule = {
  id: 'J16',
  nome: 'Leitura Diagonal Jurídica',
  tipo: 'OAB_STRATEGY',
  objetivo: 'Ler questões longas rapidamente sem perder informação essencial.',
  gatilhos: ['tempo_excessivo', 'conteudoDificil'],
  algoritmo: [
    'Ler primeiro: comando da questão (o que está sendo pedido)',
    'Ler segundo: alternativas (delimitar escopo)',
    'Ler terceiro: enunciado focando em palavras-chave',
    'Ignorar informações irrelevantes',
    'Treinar com questões progressivamente mais longas'
  ],
  acoesRetorno: ['gerar_explicacao', 'gerar_drill'],
  fonte: 'Técnicas de Leitura Rápida',
  prioridade: 7,
  areasAlvo: ['all'],
  tags: ['leitura', 'velocidade', 'eficiência', 'foco']
};

const J17: EngineModule = {
  id: 'J17',
  nome: 'Engenharia Reversa da Banca',
  tipo: 'OAB_STRATEGY',
  objetivo: 'Entender como a banca elabora questões para antecipar pegadinhas.',
  gatilhos: ['erro_repetido', 'conteudoDificil'],
  algoritmo: [
    'Identificar padrão: banca adora cobrar exceções, não regra',
    'Mapear estrutura típica: situação fática + pergunta + alternativas com pegadinha',
    'Treinar pensar como elaborador: qual erro eu quero induzir?',
    'Analisar questões passadas da mesma banca',
    'Criar questões ao estilo da banca'
  ],
  acoesRetorno: ['gerar_explicacao', 'gerar_drill'],
  fonte: 'Análise de Bancas Examinadoras',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['banca', 'padrões', 'engenharia_reversa', 'estratégia']
};

const J18: EngineModule = {
  id: 'J18',
  nome: 'Protocolo Antiansiedade Pré-Prova',
  tipo: 'EMOTIONAL',
  objetivo: 'Reduzir ansiedade e preparar mentalmente para o dia da prova.',
  gatilhos: ['ansiedade', 'simulado_iniciado', 'baixa_confiança'],
  algoritmo: [
    'Detectar sinais de ansiedade (respostas rápidas sem ler, muitos erros)',
    'Ativar protocolo respiração 4-7-8 (inspire 4s, segure 7s, expire 8s)',
    'Perguntar: O que você PODE controlar agora? (focar no controlável)',
    'Reforçar identidade: Você está preparado',
    'Redirecionar para questão fácil (micro-vitória)'
  ],
  acoesRetorno: ['ativar_respiracao', 'mostrar_mensagem', 'apresentar_questao_facil'],
  fonte: 'Psicologia de Provas + Controle Emocional',
  prioridade: 10,
  areasAlvo: ['all'],
  tags: ['ansiedade', 'emocional', 'respiração', 'controle']
};

const J19: EngineModule = {
  id: 'J19',
  nome: 'Ordem Estratégica de Resolução',
  tipo: 'OAB_STRATEGY',
  objetivo: 'Definir ordem ideal: começar por disciplina forte, não pela ordem da prova.',
  gatilhos: ['simulado_iniciado', 'inicio_sessao'],
  algoritmo: [
    'Identificar disciplinas fortes do aluno',
    'Sugerir: comece pelas fortes (confiança)',
    'Intercalar forte → fraca → forte',
    'Deixar Ética para o final (geralmente mais fáceis)',
    'Treinar essa ordem em simulados'
  ],
  acoesRetorno: ['mostrar_mensagem', 'ajustar_rotina'],
  fonte: 'Estratégia de Ordem de Resolução',
  prioridade: 7,
  areasAlvo: ['all'],
  tags: ['ordem', 'estratégia', 'confiança', 'prova']
};

const J20: EngineModule = {
  id: 'J20',
  nome: 'Revisão Inteligente de Marcadas',
  tipo: 'OAB_STRATEGY',
  objetivo: 'Protocolo eficiente para revisar questões marcadas nos últimos 30min.',
  gatilhos: ['simulado_iniciado', 'tempo_excessivo'],
  algoritmo: [
    'Últimos 30min: revisar questões marcadas',
    'Prioridade: questões que eliminou até 2 alternativas',
    'Reler só enunciado + alternativas finais (não ler tudo de novo)',
    'Decidir em até 2min ou confirmar chute inteligente',
    'Últimos 5min: conferir cartão resposta'
  ],
  acoesRetorno: ['mostrar_mensagem', 'gerar_explicacao'],
  fonte: 'Protocolo de Revisão Final',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['revisão', 'tempo', 'prova', 'protocolo']
};

// ============================================================
// MÓDULOS 21-30: CONSTRUÇÃO DE PEÇAS (2ª FASE)
// ============================================================

const J21: EngineModule = {
  id: 'J21',
  nome: 'Anatomia da Peça Jurídica',
  tipo: 'PECA_CONSTRUCTION',
  objetivo: 'Ensinar estrutura formal completa de cada tipo de peça.',
  gatilhos: ['peca_iniciada', 'duvida'],
  algoritmo: [
    'Identificar tipo de peça (petição inicial, contestação, recurso, HC, MS)',
    'Mostrar estrutura canônica: endereçamento, qualificação, fatos, fundamentos, pedido',
    'Explicar requisitos formais (CPC, CP, CLT)',
    'Mostrar checklist de verificação',
    'Exemplificar com peça-modelo comentada'
  ],
  acoesRetorno: ['gerar_checklist_peca', 'gerar_explicacao', 'mostrar_mensagem'],
  fonte: 'Prática Jurídica + Manual de Peças',
  prioridade: 9,
  areasAlvo: ['all'],
  tags: ['peça', 'estrutura', 'anatomia', 'forma']
};

const J22: EngineModule = {
  id: 'J22',
  nome: 'Checklist Inteligente de Peça',
  tipo: 'PECA_CONSTRUCTION',
  objetivo: 'Verificar se peça atende todos os requisitos antes de finalizar.',
  gatilhos: ['peca_concluida', 'peca_iniciada'],
  algoritmo: [
    'Gerar checklist específico do tipo de peça',
    'Requisitos formais: endereçamento, qualificação, assinatura',
    'Requisitos materiais: fatos, fundamentos legais, pedido claro',
    'Verificação automatizada: presença de artigos, coerência, clareza',
    'Alertar sobre erros fatais'
  ],
  acoesRetorno: ['verificar_peca', 'gerar_checklist_peca', 'mostrar_mensagem'],
  fonte: 'Rubrica de Correção OAB',
  prioridade: 10,
  areasAlvo: ['all'],
  tags: ['checklist', 'verificação', 'requisitos', 'peça']
};

const J23: EngineModule = {
  id: 'J23',
  nome: 'Fundamentação Jurídica Robusta',
  tipo: 'PECA_CONSTRUCTION',
  objetivo: 'Ensinar a fundamentar com lei + doutrina + jurisprudência de forma convincente.',
  gatilhos: ['peca_iniciada', 'duvida', 'erro_fatal_peca'],
  algoritmo: [
    'Identificar tese principal da peça',
    'Buscar fundamentos legais (artigos específicos)',
    'Complementar com jurisprudência (súmulas, precedentes)',
    'Opcional: citar doutrina de referência',
    'Estruturar: norma → interpretação → aplicação ao caso',
    'Evitar fundamentação genérica ou vaga'
  ],
  acoesRetorno: ['sugerir_fundamentacao', 'mostrar_jurisprudencia', 'gerar_explicacao'],
  fonte: 'Técnica de Fundamentação Jurídica',
  prioridade: 9,
  areasAlvo: ['all'],
  tags: ['fundamentação', 'lei', 'jurisprudência', 'argumentação']
};

const J24: EngineModule = {
  id: 'J24',
  nome: 'Fatos Jurídicos vs Irrelevantes',
  tipo: 'PECA_CONSTRUCTION',
  objetivo: 'Ensinar a selecionar fatos jurídicos relevantes e descartar o resto.',
  gatilhos: ['peca_iniciada', 'duvida'],
  algoritmo: [
    'Listar todos os fatos do caso prático',
    'Classificar: fato constitutivo, impeditivo, modificativo, extintivo',
    'Descartar fatos irrelevantes',
    'Organizar fatos em ordem cronológica lógica',
    'Narrar de forma objetiva e clara'
  ],
  acoesRetorno: ['gerar_explicacao', 'gerar_checklist_peca'],
  fonte: 'Teoria dos Fatos Jurídicos',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['fatos', 'narrativa', 'seleção', 'relevância']
};

const J25: EngineModule = {
  id: 'J25',
  nome: 'Pedido Claro e Viável',
  tipo: 'PECA_CONSTRUCTION',
  objetivo: 'Formular pedido tecnicamente correto, claro e possível.',
  gatilhos: ['peca_iniciada', 'erro_fatal_peca'],
  algoritmo: [
    'Identificar o que se quer obter com a peça',
    'Distinguir pedido mediato (bem da vida) de imediato (providência jurisdicional)',
    'Formular de forma específica e determinada',
    'Verificar se pedido é juridicamente possível',
    'Incluir pedidos subsidiários quando cabível'
  ],
  acoesRetorno: ['gerar_explicacao', 'verificar_peca'],
  fonte: 'Teoria do Pedido (CPC)',
  prioridade: 9,
  areasAlvo: ['all'],
  tags: ['pedido', 'clareza', 'viabilidade', 'técnica']
};

const J26: EngineModule = {
  id: 'J26',
  nome: 'Erros Fatais em Peças',
  tipo: 'PECA_CONSTRUCTION',
  objetivo: 'Identificar e evitar erros que zeram a nota da peça.',
  gatilhos: ['peca_iniciada', 'erro_fatal_peca'],
  algoritmo: [
    'Catalogar erros fatais por tipo de peça',
    'Exemplos: pedido impossível, ilegitimidade, incompetência absoluta, falta de fundamentação',
    'Alertar durante construção da peça',
    'Mostrar exemplos de peças zeradas',
    'Checklist final: zero erros fatais'
  ],
  acoesRetorno: ['verificar_peca', 'mostrar_mensagem', 'gerar_explicacao'],
  fonte: 'Análise de Peças Reprovadas OAB',
  prioridade: 10,
  areasAlvo: ['all'],
  tags: ['erros_fatais', 'peça', 'reprovação', 'cuidado']
};

const J27: EngineModule = {
  id: 'J27',
  nome: 'Linguagem Jurídica Adequada',
  tipo: 'PECA_CONSTRUCTION',
  objetivo: 'Escrever com clareza, correção e formalidade adequada, sem rebuscamento.',
  gatilhos: ['peca_iniciada', 'peca_concluida'],
  algoritmo: [
    'Evitar prolixidade: ser claro e direto',
    'Usar terminologia técnica correta (sem erros conceituais)',
    'Evitar arcaísmos e latinórios desnecessários',
    'Usar conectivos lógicos (portanto, todavia, outrossim)',
    'Revisar gramática e ortografia'
  ],
  acoesRetorno: ['verificar_peca', 'gerar_explicacao'],
  fonte: 'Português Jurídico',
  prioridade: 7,
  areasAlvo: ['all'],
  tags: ['linguagem', 'clareza', 'técnica', 'redação']
};

const J28: EngineModule = {
  id: 'J28',
  nome: 'Simulação de Peça Guiada',
  tipo: 'PECA_CONSTRUCTION',
  objetivo: 'Construir peça passo a passo com IA guiando cada etapa.',
  gatilhos: ['peca_iniciada', 'duvida'],
  algoritmo: [
    'Passo 1: Analisar caso prático (IA pergunta: qual o problema?)',
    'Passo 2: Identificar ação cabível (IA sugere opções)',
    'Passo 3: Selecionar fatos relevantes (IA valida)',
    'Passo 4: Fundamentar (IA sugere artigos)',
    'Passo 5: Formular pedido (IA revisa)',
    'Passo 6: Checklist final (IA verifica)'
  ],
  acoesRetorno: ['gerar_explicacao', 'gerar_checklist_peca', 'verificar_peca'],
  fonte: 'Metodologia Socrática Aplicada',
  prioridade: 9,
  areasAlvo: ['all'],
  tags: ['guiado', 'passo_a_passo', 'construção', 'didática']
};

const J29: EngineModule = {
  id: 'J29',
  nome: 'Banco de Peças-Modelo Comentadas',
  tipo: 'PECA_CONSTRUCTION',
  objetivo: 'Fornecer exemplos de peças nota 10 com comentários explicativos.',
  gatilhos: ['peca_iniciada', 'duvida'],
  algoritmo: [
    'Identificar tipo de peça que aluno vai fazer',
    'Mostrar peça-modelo nota 10',
    'Comentar cada parte: por que está correto',
    'Destacar diferenciais que garantiram nota máxima',
    'Permitir comparação com peça do aluno'
  ],
  acoesRetorno: ['gerar_explicacao', 'mostrar_mensagem'],
  fonte: 'Banco de Peças Aprovadas OAB',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['modelo', 'exemplo', 'nota_10', 'referência']
};

const J30: EngineModule = {
  id: 'J30',
  nome: 'Correção Detalhada de Peça',
  tipo: 'PECA_CONSTRUCTION',
  objetivo: 'Fornecer feedback detalhado por competência (forma, conteúdo, técnica).',
  gatilhos: ['peca_concluida'],
  algoritmo: [
    'Avaliar forma (0-2 pontos): endereçamento, qualificação, assinatura',
    'Avaliar conteúdo (0-4 pontos): fatos, fundamentos, pedido',
    'Avaliar fundamentação (0-2 pontos): lei + jurisprudência',
    'Avaliar técnica (0-2 pontos): linguagem, coerência, clareza',
    'Gerar nota (0-10) e feedback específico',
    'Listar erros e sugestões de melhoria',
    'Indicar se necessita refazer'
  ],
  acoesRetorno: ['verificar_peca', 'gerar_explicacao', 'mostrar_mensagem'],
  fonte: 'Rubrica de Correção OAB Oficial',
  prioridade: 10,
  areasAlvo: ['all'],
  tags: ['correção', 'feedback', 'avaliação', 'nota']
};

// ============================================================
// MÓDULOS 31-40: ORGANIZAÇÃO E PRODUTIVIDADE
// ============================================================

const J31: EngineModule = {
  id: 'J31',
  nome: 'Planejamento Reverso até a OAB',
  tipo: 'ORGANIZATION',
  objetivo: 'Criar cronograma de estudos partindo da data da prova.',
  gatilhos: ['inicio_sessao'],
  algoritmo: [
    'Calcular dias até a prova OAB',
    'Dividir disciplinas proporcionalmente (considerar peso)',
    'Ajustar para fraquezas do aluno (dobrar tempo em fracas)',
    'Reservar 2 semanas finais para simulados e revisão',
    'Reorganizar semanalmente baseado em performance'
  ],
  acoesRetorno: ['mostrar_mensagem', 'ajustar_rotina'],
  fonte: 'Planejamento Estratégico de Estudos',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['planejamento', 'cronograma', 'reverso', 'OAB']
};

const J32: EngineModule = {
  id: 'J32',
  nome: 'Blocos Pomodoro Jurídico',
  tipo: 'PRODUCTIVITY',
  objetivo: 'Maximizar foco com blocos de 50min estudo + 10min pausa.',
  gatilhos: ['inicio_sessao', 'bloco_completo'],
  algoritmo: [
    'Criar bloco de 50min com pausa de 10min (adaptado ao Direito)',
    'Monitorar atenção (taxa de erro, tempo de resposta)',
    'Se atenção cair, recomendar pausa antecipada',
    'A cada 4 blocos (4h), pausa longa de 30min',
    'Registrar performance do bloco'
  ],
  acoesRetorno: ['mostrar_mensagem', 'sugerir_pausa'],
  fonte: 'Técnica Pomodoro Adaptada',
  prioridade: 7,
  areasAlvo: ['all'],
  tags: ['pomodoro', 'foco', 'blocos', 'pausa']
};

const J33: EngineModule = {
  id: 'J33',
  nome: 'Regra 70-30 (Teoria + Prática)',
  tipo: 'PRODUCTIVITY',
  objetivo: 'Garantir equilíbrio: 30% teoria + 70% questões.',
  gatilhos: ['bloco_completo', 'inicio_sessao'],
  algoritmo: [
    'Rastrear tempo de teoria vs prática',
    'Meta: 30% leitura de ontologia/lei seca, 70% questões',
    'Recomendar prática após 20min de teoria',
    'Registrar erros para revisão espaçada',
    'Ajustar proporção se performance cair'
  ],
  acoesRetorno: ['gerar_drill', 'sugerir_revisao', 'mostrar_mensagem'],
  fonte: 'Metodologia Ativa de Aprendizagem',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['teoria', 'prática', 'equilíbrio', 'questões']
};

const J34: EngineModule = {
  id: 'J34',
  nome: 'Ritual de Início de Sessão',
  tipo: 'ORGANIZATION',
  objetivo: 'Começar estudo com clareza de objetivos e foco.',
  gatilhos: ['inicio_sessao'],
  algoritmo: [
    'Mostrar 3 prioridades do dia',
    'Exibir progresso geral (% até aprovação)',
    'Questão de aquecimento (fácil) para ganhar confiança',
    'Ativar timer e eliminar distrações',
    'Reforçar identidade: Você é aprovado'
  ],
  acoesRetorno: ['mostrar_mensagem', 'apresentar_questao_facil', 'mostrar_progresso'],
  fonte: 'Ritual de Início',
  prioridade: 7,
  areasAlvo: ['all'],
  tags: ['ritual', 'início', 'foco', 'clareza']
};

const J35: EngineModule = {
  id: 'J35',
  nome: 'Ritual de Encerramento de Sessão',
  tipo: 'ORGANIZATION',
  objetivo: 'Fechar sessão consolidando aprendizado e planejando próxima.',
  gatilhos: ['fim_sessao'],
  algoritmo: [
    'Revisar 3 conceitos do dia com quiz rápido',
    'Gerar flashcards automáticos dos erros',
    'Identificar 1 erro estrutural e sugerir reforço',
    'Planejar próxima sessão (temas + tempo)',
    'Comemorar: FP ganhos, streak, progresso'
  ],
  acoesRetorno: ['gerar_drill', 'criar_flashcards', 'ajustar_rotina', 'mostrar_progresso'],
  fonte: 'Ritual de Encerramento',
  prioridade: 7,
  areasAlvo: ['all'],
  tags: ['ritual', 'encerramento', 'consolidação', 'planejamento']
};

const J36: EngineModule = {
  id: 'J36',
  nome: 'Mapa de Calor de Conhecimento',
  tipo: 'ORGANIZATION',
  objetivo: 'Visualizar graficamente pontos fortes e fracos por disciplina.',
  gatilhos: ['fim_sessao', 'simulado_concluido'],
  algoritmo: [
    'Gerar mapa visual: verde (domínio), amarelo (médio), vermelho (fraco)',
    'Por disciplina e sub-tópico',
    'Atualizar em tempo real',
    'Sugerir foco nas áreas vermelhas',
    'Comemorar transição vermelho → amarelo → verde'
  ],
  acoesRetorno: ['mostrar_progresso', 'ajustar_rotina'],
  fonte: 'Visualização de Progresso',
  prioridade: 6,
  areasAlvo: ['all'],
  tags: ['mapa_calor', 'visual', 'progresso', 'pontos_fracos']
};

const J37: EngineModule = {
  id: 'J37',
  nome: 'Protocolo de Procrastinação',
  tipo: 'EMOTIONAL',
  objetivo: 'Combater procrastinação com microblocos de 2min.',
  gatilhos: ['procrastinação', 'travamento'],
  algoritmo: [
    'Detectar inatividade longa (dias sem estudar)',
    'Dividir em microbloco de 2min: só 1 questão',
    'Perguntar: Você consegue fazer 1 questão agora?',
    'Completar e celebrar micro-vitória',
    'Aumentar progressivamente até 50min'
  ],
  acoesRetorno: ['mostrar_mensagem', 'apresentar_questao_facil', 'ajustar_rotina'],
  fonte: 'Psicologia da Procrastinação',
  prioridade: 9,
  areasAlvo: ['all'],
  tags: ['procrastinação', 'microbloco', 'início', 'momentum']
};

const J38: EngineModule = {
  id: 'J38',
  nome: 'Identidade de Aprovado',
  tipo: 'EMOTIONAL',
  objetivo: 'Reforçar mentalidade de aprovação e autoeficácia.',
  gatilhos: ['baixa_confiança', 'frustração', 'inicio_sessao'],
  algoritmo: [
    'Perguntar: Por que você PRECISA passar na OAB?',
    'Gerar frase de identidade: Eu sou o tipo de pessoa que [estuda todo dia / não desiste / domina Direito]',
    'Reforçar identidade quando confiança baixa',
    'Rastrear consistência psicológica semanal',
    'Comemorar pequenas vitórias'
  ],
  acoesRetorno: ['mostrar_mensagem', 'reforçar_identidade'],
  fonte: 'Psicologia da Autoeficácia',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['identidade', 'motivação', 'aprovação', 'mentalidade']
};

const J39: EngineModule = {
  id: 'J39',
  nome: 'Detecção de Regressão',
  tipo: 'HIGH_PERFORMANCE',
  objetivo: 'Detectar quando aluno regride em tema já dominado e intervir.',
  gatilhos: ['erro_repetido', 'queda_rendimento'],
  algoritmo: [
    'Monitorar temas com >80% de acerto',
    'Se acerto cair abaixo de 70%, alertar regressão',
    'Investigar causa: falta de revisão, confusão conceitual',
    'Agendar revisão emergencial',
    'Drill focado até recuperar nível'
  ],
  acoesRetorno: ['mostrar_mensagem', 'gerar_drill', 'agendar_revisao'],
  fonte: 'Análise de Performance',
  prioridade: 8,
  areasAlvo: ['all'],
  tags: ['regressão', 'monitoramento', 'performance', 'revisão']
};

const J40: EngineModule = {
  id: 'J40',
  nome: 'Antifrágil Jurídico',
  tipo: 'HIGH_PERFORMANCE',
  objetivo: 'Transformar erros em força: cada erro vira oportunidade de domínio.',
  gatilhos: ['erro_repetido', 'frustração'],
  algoritmo: [
    'Detectar erro repetido (3x mesmo padrão)',
    'Mensagem: Este erro vai te tornar MAIS forte',
    'Criar explicação personalizada com analogias',
    'Gerar drill corretivo de 10 questões',
    'Agendar reavaliação em 7 dias',
    'Comemorar quando dominar: Você é antifrágil!'
  ],
  acoesRetorno: ['gerar_drill', 'mostrar_mensagem', 'agendar_revisao', 'gerar_explicacao'],
  fonte: 'Antifrágil (Nassim Taleb) aplicado ao Direito',
  prioridade: 9,
  areasAlvo: ['all'],
  tags: ['antifrágil', 'erro', 'resiliência', 'crescimento']
};

// ============================================================
// EXPORTS
// ============================================================

export const ENGINE_MODULES: EngineModule[] = [
  J01, J02, J03, J04, J05, J06, J07, J08, J09, J10,
  J11, J12, J13, J14, J15, J16, J17, J18, J19, J20,
  J21, J22, J23, J24, J25, J26, J27, J28, J29, J30,
  J31, J32, J33, J34, J35, J36, J37, J38, J39, J40,
];

/**
 * Busca módulos por gatilho
 */
export function getModulesByTrigger(trigger: string): EngineModule[] {
  return ENGINE_MODULES.filter(m => m.gatilhos.includes(trigger));
}

/**
 * Busca módulo por ID
 */
export function getModuleById(id: string): EngineModule | undefined {
  return ENGINE_MODULES.find(m => m.id === id);
}

/**
 * Busca módulos por tipo
 */
export function getModulesByType(type: ModuleType): EngineModule[] {
  return ENGINE_MODULES.filter(m => m.tipo === type);
}

/**
 * Busca módulos por área
 */
export function getModulesByArea(area: string): EngineModule[] {
  return ENGINE_MODULES.filter(m =>
    m.areasAlvo.includes('all') || m.areasAlvo.includes(area as any)
  );
}
