# 🎨 Requisitos de Assets - Conductor Quest

## 📦 Overview

Este documento lista todos os assets visuais e sonoros necessários para o MVP do Conductor Quest, priorizando a reutilização e simplicidade.

---

## 🏛️ AMBIENTE - O Salão da Guilda

### Background Principal

```
Arquivo: guild-hall-bg.png
Dimensões: 1024x768px (base)
Estilo: Medieval-fantástico com toques tech
Elementos:
- Piso de pedra com runas iluminadas
- Paredes de pedra com telas holográficas
- Teto alto com vitrais digitais
- Iluminação quente ambiente
```

### Áreas Específicas

#### 1. Centro do Salão
```
Arquivo: hall-center.png
- Círculo de invocação no chão
- Pedestal para o Guia
- Iluminação focal
```

#### 2. Mesa do Escriba
```
Arquivo: scribe-desk.png
- Mesa de madeira antiga
- Pergaminhos flutuantes (animados)
- Pena mágica
- Hologramas de diagramas
```

#### 3. Forja da Artesã
```
Arquivo: artisan-forge.png
- Bigorna tecnológica
- Ferramentas penduradas
- Faíscas particle system
- Parede para projeção (canvas)
```

#### 4. Galeria da Crítica
```
Arquivo: critic-gallery.png
- Paredes com quadros elegantes
- Iluminação de galeria
- Pedestal de observação
- Atmosfera refinada
```

#### 5. Portão Principal
```
Arquivo: main-gate.png
Estados:
- gate-closed.png (início)
- gate-opening.png (sprite sheet animação)
- gate-open.png (final)
```

---

## 👥 PERSONAGENS (NPCs)

### Estilo Visual Geral
- **Opção A**: Pixel Art (32x32 ou 64x64)
- **Opção B**: Low Poly 2D
- **Cores**: Vibrantes mas não saturadas

### 1. O Guia

```
Arquivos:
- guide-idle.png (sprite sheet 4 frames)
- guide-talking.png (sprite sheet 4 frames)
- guide-gesturing.png (animação especial)

Visual:
- Robes modernos (azul e dourado)
- Barba branca estilizada
- Cajado com cristal brilhante
- Aura sutil de sabedoria
```

### 2. O Escriba

```
Arquivos:
- scribe-idle.png (sprite sheet)
- scribe-writing.png (sprite sheet)
- scribe-thinking.png (pose estática)

Visual:
- Óculos redondos
- Roupa de estudioso (marrom/bege)
- Pena mágica sempre em mão
- Pergaminho flutuante ao lado
```

### 3. A Artesã

```
Arquivos:
- artisan-idle.png (sprite sheet)
- artisan-working.png (sprite sheet 6 frames)
- artisan-celebrating.png (pose vitória)

Visual:
- Avental de couro tech
- Cabelo preso, prático
- Martelo luminoso
- Óculos de proteção no topo da cabeça
```

### 4. A Crítica

```
Arquivos:
- critic-idle.png (sprite sheet)
- critic-observing.png (sprite sheet)
- critic-approving.png (sorriso sutil)

Visual:
- Vestimenta elegante (roxo/preto)
- Monóculo dourado
- Postura refinada
- Prancheta holográfica
```

### 5. O Iniciado (Player)

```
Arquivos:
- player-idle.png (sprite sheet)
- player-walk.png (sprite sheet 8 frames)
- player-transformed.png (versão Condutor)

Visual:
- Design neutro/customizável
- Roupas simples (início)
- Roupas ornamentadas (final)
- Indicador de seleção (círculo sob os pés)
```

---

## 🎯 ELEMENTOS INTERATIVOS

### Indicadores

```
UI Elements:
- exclamation-mark.png (! sobre NPCs)
- question-mark.png (? para dúvidas)
- chat-bubble.png (💬 indicador)
- glow-circle.png (seleção/hover)
- footsteps.png (sprite sheet pegadas)
```

### Estandarte (Hero Asset)

```
Banner Creation:
- banner-frame.png (moldura)
- star-golden.png (estrela central)
- gradient-bg.png (fundo)

Animação de Criação:
- pixel-buildup-sheet.png (30 frames)
- particle-gold.png (partículas douradas)
- shine-effect.png (brilho final)
```

---

## 🎨 INTERFACE (UI)

### Modal de Chat

```
Chat UI:
- parchment-bg.png (fundo pergaminho)
- parchment-border.png (bordas decoradas)
- chat-header.png
- option-button.png (normal/hover/selected)
- typing-indicator.gif (3 pontos animados)
```

### Quest Tracker

```
Quest UI:
- quest-panel-bg.png
- checkbox-empty.png
- checkbox-checked.png
- progress-bar-empty.png
- progress-bar-fill.png
- quest-icon.png (🎯)
```

### Elementos Gerais

```
General UI:
- button-primary.png (estados: normal/hover/pressed)
- button-secondary.png
- panel-bg-wood.png
- divider-ornate.png
- corner-decoration.png
```

---

## ✨ EFEITOS VISUAIS (VFX)

### Partículas

```
Particles:
- sparkle-yellow.png (sprite sheet)
- dust-magical.png
- glow-soft.png
- fire-spark.png (forja)
- light-ray.png (transformação)
```

### Animações Especiais

```
Special FX:
- magic-circle-activate.png (sprite sheet)
- level-up-burst.png (sprite sheet)
- portal-opening.png (sprite sheet)
- aura-glow.png (animated)
```

---

## 🎵 ÁUDIO

### Música de Fundo

```
BGM (loops):
- bgm-ambient-hall.ogg (2-3 min loop)
- bgm-working.ogg (durante criação)
- bgm-success.ogg (vitória, 30s)
- bgm-transformation.ogg (final épico, 1 min)
```

### Efeitos Sonoros

```
SFX Essenciais:
- footstep-stone.wav (passos)
- npc-greeting.wav (sino suave)
- chat-open.wav (pergaminho abrindo)
- writing-quill.wav (escriba escrevendo)
- hammer-forge.wav (artesã trabalhando)
- magic-sparkle.wav (criação)
- quest-complete.wav (fanfarra curta)
- transformation.wav (crescendo épico)
- gate-opening.wav (rangido + mágica)
```

### Vozes (Opcional)

```
Voice Gibberish:
- guide-greeting.wav ("Hmm-hmm!")
- scribe-thinking.wav ("Ah-ha...")
- artisan-excited.wav ("Yeah!")
- critic-analyzing.wav ("Hmm...")
```

---

## 📱 ASSETS MOBILE-SPECIFIC

### Ícones Touch

```
Touch UI:
- touch-indicator.png (círculo de toque)
- drag-arrow.png (indicador de drag)
- pinch-icon.png (tutorial zoom)
```

### Loading Screens

```
Loading:
- loading-bg-mobile.png (portrait)
- loading-spinner.gif
- tips-bg.png (dicas durante loading)
```

---

## 🎯 PRIORIZAÇÃO PARA MVP

### 🔴 CRÍTICO (Sem isso não funciona)
1. Background do salão
2. 4 NPCs básicos (idle + talking)
3. Player sprite (idle + walk)
4. Modal de chat
5. Quest tracker básico
6. Efeito de criação do estandarte
7. SFX essenciais (5-6 sons)

### 🟡 IMPORTANTE (Melhora muito a experiência)
1. Animações dos NPCs working
2. Partículas básicas
3. Música ambiente
4. Indicadores visuais (!, 💬)
5. Transformação visual do player

### 🟢 NICE TO HAVE (Polish)
1. Vozes gibberish
2. Múltiplas músicas
3. Todos os efeitos visuais
4. Animações complexas
5. Customização visual

---

## 🛠️ ESPECIFICAÇÕES TÉCNICAS

### Formatos
- **Imagens**: PNG (com transparência)
- **Sprite Sheets**: PNG com grid uniforme
- **Áudio**: OGG Vorbis (melhor compressão)
- **Fallback**: MP3 para compatibilidade

### Resolução
- **Base Canvas**: 1024x768
- **Sprites**: Múltiplos de 32px
- **UI Elements**: Mínimo 44x44px (touch)

### Otimização
- **Sprite Atlas**: Combinar sprites pequenos
- **Compressão**: TinyPNG para imagens
- **Audio Sprites**: Combinar SFX curtos
- **Lazy Loading**: Carregar sob demanda

---

## 💰 ALTERNATIVAS LOW-COST

### Assets Gratuitos/Open Source

1. **OpenGameArt.org**
   - Medieval sprites
   - UI elements
   - Particle effects

2. **Freesound.org**
   - SFX biblioteca
   - Música royalty-free

3. **Emoji Fallback**
   - Usar emojis como sprites temporários
   - 🧙‍♂️👨‍🏫👩‍🎨👩‍💼 para NPCs

### Geração Procedural

```javascript
// Gerar backgrounds simples
function generateGuildHall() {
  // Canvas API para criar:
  - Piso de pedra (pattern)
  - Gradientes para paredes
  - Círculos para luz
}

// Partículas via código
function createParticles() {
  // Canvas circles com glow
  // Sem precisar de imagens
}
```

---

## 📋 CHECKLIST DE PRODUÇÃO

### Fase 1: Assets Essenciais
- [ ] Background principal
- [ ] 4 NPCs (versão básica)
- [ ] Player sprite
- [ ] UI do chat
- [ ] 3-5 SFX principais

### Fase 2: Momento Hero
- [ ] Animação do estandarte
- [ ] Partículas douradas
- [ ] Som de criação
- [ ] Efeito de conclusão

### Fase 3: Polish
- [ ] Todas animações
- [ ] Música completa
- [ ] Todos SFX
- [ ] Efeitos visuais
- [ ] Tela de vitória

---

## 🎨 DIREÇÃO DE ARTE - REFERÊNCIAS

### Estilo Visual
- **Inspiração**: Stardew Valley meets Hades
- **Paleta**: Quente e acolhedora com toques de magia
- **Mood**: Profissional mas mágico, sério mas acessível

### Referências Visuais
1. **Ambiente**: Hogwarts Legacy (salões)
2. **NPCs**: Stardew Valley (pixel art expressivo)
3. **UI**: Slay the Spire (cards e painéis)
4. **VFX**: Hades (partículas e brilhos)

---

*Com estes assets, o Conductor Quest terá uma identidade visual única e memorável, mantendo-se viável para produção rápida.* 🎨✨