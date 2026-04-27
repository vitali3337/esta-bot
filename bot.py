<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ESTA Realty — AI Консьерж</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Jost:wght@200;300;400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --gold: #c9a84c;
    --gold-light: #e4c97a;
    --gold-dim: rgba(201,168,76,0.15);
    --bg: #0d0d0d;
    --bg2: #141414;
    --bg3: #1c1c1c;
    --surface: #191919;
    --border: rgba(201,168,76,0.2);
    --text: #f0ece4;
    --text-dim: rgba(240,236,228,0.5);
    --text-faint: rgba(240,236,228,0.25);
  }

  html, body {
    height: 100%;
    background: var(--bg);
    color: var(--text);
    font-family: 'Jost', sans-serif;
    font-weight: 300;
    overflow: hidden;
  }

  /* ── Layout ── */
  .app {
    display: grid;
    grid-template-columns: 280px 1fr;
    grid-template-rows: 100vh;
    height: 100vh;
  }

  /* ── Sidebar ── */
  .sidebar {
    background: var(--bg2);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow: hidden;
    position: relative;
  }

  .sidebar::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 300px;
    background: radial-gradient(ellipse at top left, rgba(201,168,76,0.08) 0%, transparent 70%);
    pointer-events: none;
  }

  .logo-area {
    padding: 36px 28px 28px;
    border-bottom: 1px solid var(--border);
  }

  .logo-badge {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
  }

  .logo-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, var(--gold), var(--gold-light));
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
  }

  .logo-text {
    font-family: 'Cormorant Garamond', serif;
    font-size: 22px;
    font-weight: 500;
    letter-spacing: 3px;
    color: var(--gold-light);
    text-transform: uppercase;
  }

  .logo-sub {
    font-size: 10px;
    letter-spacing: 2.5px;
    color: var(--text-dim);
    text-transform: uppercase;
    font-weight: 400;
  }

  .ai-status {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 14px;
    font-size: 11px;
    color: var(--text-dim);
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .ai-dot {
    width: 7px; height: 7px;
    background: #4caf50;
    border-radius: 50%;
    animation: pulse 2s infinite;
    box-shadow: 0 0 8px rgba(76,175,80,0.5);
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(0.85); }
  }

  /* Quick topics */
  .quick-section {
    padding: 24px 20px 16px;
    flex: 1;
    overflow-y: auto;
  }

  .quick-section::-webkit-scrollbar { width: 3px; }
  .quick-section::-webkit-scrollbar-track { background: transparent; }
  .quick-section::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .section-label {
    font-size: 9px;
    letter-spacing: 3px;
    color: var(--text-faint);
    text-transform: uppercase;
    margin-bottom: 12px;
    padding: 0 8px;
  }

  .topic-btn {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    padding: 11px 14px;
    margin-bottom: 4px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    color: var(--text-dim);
    font-family: 'Jost', sans-serif;
    font-size: 13px;
    font-weight: 300;
    text-align: left;
    cursor: pointer;
    transition: all 0.2s ease;
    letter-spacing: 0.3px;
  }

  .topic-btn:hover {
    background: var(--gold-dim);
    border-color: var(--border);
    color: var(--text);
  }

  .topic-icon {
    font-size: 15px;
    width: 20px;
    text-align: center;
    flex-shrink: 0;
  }

  /* Property cards */
  .prop-section {
    padding: 0 20px 20px;
  }

  .prop-card {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.25s;
  }

  .prop-card:hover {
    border-color: var(--gold);
    background: var(--surface);
    transform: translateX(3px);
  }

  .prop-type {
    font-size: 9px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 4px;
  }

  .prop-name {
    font-family: 'Cormorant Garamond', serif;
    font-size: 15px;
    font-weight: 500;
    color: var(--text);
    margin-bottom: 2px;
  }

  .prop-price {
    font-size: 12px;
    color: var(--text-dim);
    font-weight: 400;
  }

  /* ── Main chat area ── */
  .chat-area {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--bg);
    position: relative;
    overflow: hidden;
  }

  /* Decorative background */
  .chat-area::before {
    content: '';
    position: absolute;
    top: -200px; right: -200px;
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(201,168,76,0.04) 0%, transparent 65%);
    pointer-events: none;
    z-index: 0;
  }

  /* Header */
  .chat-header {
    padding: 20px 32px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(13,13,13,0.9);
    backdrop-filter: blur(10px);
    position: relative;
    z-index: 10;
    flex-shrink: 0;
  }

  .chat-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 20px;
    font-weight: 400;
    font-style: italic;
    color: var(--text);
    letter-spacing: 0.5px;
  }

  .chat-title span {
    color: var(--gold);
    font-style: normal;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .header-btn {
    padding: 7px 16px;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 20px;
    color: var(--text-dim);
    font-family: 'Jost', sans-serif;
    font-size: 11px;
    font-weight: 400;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s;
  }

  .header-btn:hover {
    border-color: var(--gold);
    color: var(--gold);
  }

  /* Messages */
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 32px 40px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    position: relative;
    z-index: 1;
  }

  .messages::-webkit-scrollbar { width: 4px; }
  .messages::-webkit-scrollbar-track { background: transparent; }
  .messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  /* Welcome */
  .welcome {
    text-align: center;
    padding: 60px 20px 40px;
    animation: fadeUp 0.8s ease both;
  }

  .welcome-ornament {
    font-family: 'Cormorant Garamond', serif;
    font-size: 64px;
    color: var(--gold);
    opacity: 0.3;
    line-height: 1;
    margin-bottom: 16px;
  }

  .welcome h1 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 36px;
    font-weight: 300;
    color: var(--text);
    letter-spacing: 2px;
    margin-bottom: 12px;
  }

  .welcome h1 em {
    color: var(--gold);
    font-style: italic;
  }

  .welcome p {
    font-size: 14px;
    color: var(--text-dim);
    max-width: 420px;
    margin: 0 auto;
    line-height: 1.7;
    font-weight: 300;
  }

  .welcome-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-top: 28px;
  }

  .chip {
    padding: 8px 18px;
    border: 1px solid var(--border);
    border-radius: 20px;
    font-size: 12px;
    color: var(--text-dim);
    cursor: pointer;
    transition: all 0.2s;
    letter-spacing: 0.5px;
    background: transparent;
    font-family: 'Jost', sans-serif;
    font-weight: 300;
  }

  .chip:hover {
    border-color: var(--gold);
    color: var(--gold);
    background: var(--gold-dim);
  }

  /* Message bubbles */
  .msg {
    display: flex;
    gap: 14px;
    animation: fadeUp 0.4s ease both;
    max-width: 780px;
  }

  .msg.user {
    flex-direction: row-reverse;
    align-self: flex-end;
  }

  .msg-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
    margin-top: 2px;
  }

  .msg.bot .msg-avatar {
    background: linear-gradient(135deg, var(--gold), var(--gold-light));
    color: #000;
  }

  .msg.user .msg-avatar {
    background: var(--bg3);
    border: 1px solid var(--border);
  }

  .msg-bubble {
    padding: 14px 18px;
    border-radius: 14px;
    font-size: 14px;
    line-height: 1.75;
    font-weight: 300;
    letter-spacing: 0.2px;
  }

  .msg.bot .msg-bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    border-top-left-radius: 4px;
    color: var(--text);
  }

  .msg.user .msg-bubble {
    background: linear-gradient(135deg, rgba(201,168,76,0.18), rgba(201,168,76,0.08));
    border: 1px solid rgba(201,168,76,0.3);
    border-top-right-radius: 4px;
    color: var(--text);
  }

  .msg-bubble strong {
    color: var(--gold-light);
    font-weight: 500;
  }

  .msg-bubble em {
    color: var(--text-dim);
  }

  .msg-bubble ul {
    margin: 8px 0 4px 18px;
  }

  .msg-bubble li {
    margin-bottom: 4px;
    color: var(--text-dim);
  }

  /* Typing indicator */
  .typing {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 14px 18px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    border-top-left-radius: 4px;
    width: fit-content;
  }

  .typing span {
    width: 7px; height: 7px;
    background: var(--gold);
    border-radius: 50%;
    animation: typingBounce 1.2s infinite;
    opacity: 0.5;
  }

  .typing span:nth-child(2) { animation-delay: 0.2s; }
  .typing span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes typingBounce {
    0%, 100% { transform: translateY(0); opacity: 0.5; }
    50% { transform: translateY(-5px); opacity: 1; }
  }

  /* Input area */
  .input-area {
    padding: 20px 40px 28px;
    border-top: 1px solid var(--border);
    background: rgba(13,13,13,0.95);
    backdrop-filter: blur(10px);
    position: relative;
    z-index: 10;
    flex-shrink: 0;
  }

  .input-wrapper {
    display: flex;
    gap: 12px;
    align-items: flex-end;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
    transition: border-color 0.2s;
  }

  .input-wrapper:focus-within {
    border-color: rgba(201,168,76,0.4);
  }

  #userInput {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-family: 'Jost', sans-serif;
    font-size: 14px;
    font-weight: 300;
    resize: none;
    line-height: 1.6;
    max-height: 120px;
    min-height: 24px;
  }

  #userInput::placeholder {
    color: var(--text-faint);
  }

  .send-btn {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--gold), var(--gold-light));
    border: none;
    border-radius: 10px;
    color: #000;
    font-size: 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    flex-shrink: 0;
  }

  .send-btn:hover { transform: scale(1.05); filter: brightness(1.1); }
  .send-btn:active { transform: scale(0.97); }
  .send-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

  .input-hint {
    font-size: 10px;
    color: var(--text-faint);
    margin-top: 10px;
    text-align: center;
    letter-spacing: 1px;
  }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* Contact card inside message */
  .contact-card {
    margin-top: 12px;
    padding: 12px 16px;
    background: var(--gold-dim);
    border: 1px solid var(--border);
    border-radius: 10px;
    font-size: 13px;
  }

  .contact-card a {
    color: var(--gold);
    text-decoration: none;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .app { grid-template-columns: 1fr; }
    .sidebar { display: none; }
    .messages { padding: 20px 16px; }
    .input-area { padding: 14px 16px 20px; }
    .chat-header { padding: 14px 16px; }
  }

  /* scrollbar for messages */
  .messages { scrollbar-width: thin; scrollbar-color: var(--border) transparent; }
</style>
</head>
<body>
<div class="app">

  <!-- ── Sidebar ── -->
  <aside class="sidebar">
    <div class="logo-area">
      <div class="logo-badge">
        <div class="logo-icon">🏛️</div>
        <div class="logo-text">ESTA</div>
      </div>
      <div class="logo-sub">Realty Group · AI Консьерж</div>
      <div class="ai-status">
        <div class="ai-dot"></div>
        ИИ онлайн
      </div>
    </div>

    <div class="quick-section">
      <div class="section-label">Быстрые запросы</div>

      <button class="topic-btn" onclick="sendQuick('Хочу купить квартиру в Тирасполе. Что посоветуете?')">
        <span class="topic-icon">🏠</span> Купить квартиру
      </button>
      <button class="topic-btn" onclick="sendQuick('Интересует аренда жилья. Какие варианты есть?')">
        <span class="topic-icon">🔑</span> Аренда жилья
      </button>
      <button class="topic-btn" onclick="sendQuick('Хочу продать свою недвижимость. С чего начать?')">
        <span class="topic-icon">💰</span> Продать объект
      </button>
      <button class="topic-btn" onclick="sendQuick('Расскажите об инвестициях в недвижимость')">
        <span class="topic-icon">📈</span> Инвестиции
      </button>
      <button class="topic-btn" onclick="sendQuick('Нужна помощь в оформлении ипотеки')">
        <span class="topic-icon">🏦</span> Ипотека
      </button>
      <button class="topic-btn" onclick="sendQuick('Коммерческая недвижимость — офисы и склады')">
        <span class="topic-icon">🏢</span> Коммерция
      </button>
      <button class="topic-btn" onclick="sendQuick('Новостройки — что сейчас строится?')">
        <span class="topic-icon">🏗️</span> Новостройки
      </button>
      <button class="topic-btn" onclick="sendQuick('Как связаться с агентом?')">
        <span class="topic-icon">📞</span> Связаться с агентом
      </button>

      <div class="section-label" style="margin-top:20px">Популярные объекты</div>
    </div>

    <div class="prop-section">
      <div class="prop-card" onclick="sendQuick('Расскажи подробнее про ЖК Премиум в центре города')">
        <div class="prop-type">Новостройка</div>
        <div class="prop-name">ЖК «Премиум»</div>
        <div class="prop-price">от $45 000 · Центр</div>
      </div>
      <div class="prop-card" onclick="sendQuick('Расскажи про загородные дома с участком')">
        <div class="prop-type">Частный дом</div>
        <div class="prop-name">Коттедж с участком</div>
        <div class="prop-price">от $80 000 · Пригород</div>
      </div>
      <div class="prop-card" onclick="sendQuick('Есть ли коммерческие помещения под бизнес?')">
        <div class="prop-type">Коммерция</div>
        <div class="prop-name">Офис / Торговля</div>
        <div class="prop-price">Аренда от $8/м²</div>
      </div>
    </div>
  </aside>

  <!-- ── Chat ── -->
  <main class="chat-area">
    <header class="chat-header">
      <div class="chat-title">AI <span>Консьерж</span> по недвижимости</div>
      <div class="header-actions">
        <button class="header-btn" onclick="clearChat()">↺ Новый чат</button>
        <button class="header-btn" onclick="sendQuick('Как связаться с агентом?')">☎ Агент</button>
      </div>
    </header>

    <div class="messages" id="messages">
      <div class="welcome" id="welcome">
        <div class="welcome-ornament">⌂</div>
        <h1>Добро пожаловать в <em>ESTA Realty</em></h1>
        <p>Ваш персональный AI‑консьерж по недвижимости. Помогу найти идеальный объект, рассчитать ипотеку, оформить сделку.</p>
        <div class="welcome-chips">
          <button class="chip" onclick="sendQuick('Хочу купить квартиру до $60 000')">🏠 Купить квартиру</button>
          <button class="chip" onclick="sendQuick('Снять жильё на длительный срок')">🔑 Снять жильё</button>
          <button class="chip" onclick="sendQuick('Оценить мою квартиру')">💎 Оценить объект</button>
          <button class="chip" onclick="sendQuick('Инвестиции в недвижимость — с чего начать?')">📈 Инвестировать</button>
          <button class="chip" onclick="sendQuick('Как проходит сделка купли-продажи?')">📋 Процесс сделки</button>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-wrapper">
        <textarea
          id="userInput"
          rows="1"
          placeholder="Спросите про любой объект, район, цену или услугу…"
          onkeydown="handleKey(event)"
          oninput="autoResize(this)"
        ></textarea>
        <button class="send-btn" id="sendBtn" onclick="sendMessage()">➤</button>
      </div>
      <div class="input-hint">Enter — отправить · Shift+Enter — новая строка</div>
    </div>
  </main>
</div>

<script>
const SYSTEM_PROMPT = `Ты — профессиональный AI-консьерж агентства недвижимости ESTA Realty. Ты эксперт в сфере недвижимости Молдовы и Приднестровья (Тирасполь, Кишинёв, Бендеры и регион).

Твоя роль:
- Помогать клиентам найти подходящий объект недвижимости (квартиры, дома, коммерческие помещения, земля)
- Консультировать по вопросам покупки, продажи и аренды
- Объяснять процесс сделки, документы, юридические нюансы
- Рассказывать про ипотеку, рассрочку, условия сделок
- Давать советы по инвестициям в недвижимость
- Отвечать на вопросы о районах, инфраструктуре, ценах

Ценовой диапазон в регионе:
- Однокомнатные квартиры: $15 000 – $45 000
- Двухкомнатные квартиры: $25 000 – $70 000
- Трёхкомнатные и больше: $40 000 – $120 000+
- Частные дома: $50 000 – $200 000+
- Коммерческие помещения: аренда от $7/м²

Стиль общения:
- Профессиональный, тёплый, экспертный
- Пиши структурированно, используй эмодзи умеренно
- Предлагай конкретные варианты действий
- В конце консультации предлагай связаться с агентом

Контакты агентства:
📞 Телефон: +7 (533) 12-34-56
💬 Telegram: @esta_realty_bot
🌐 Сайт: esta-realty.com
📍 Офис: Тирасполь, ул. Ленина, 22`;

let history = [];
let isLoading = false;

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function sendQuick(text) {
  document.getElementById('userInput').value = text;
  sendMessage();
}

function clearChat() {
  history = [];
  const msgs = document.getElementById('messages');
  msgs.innerHTML = `
    <div class="welcome" id="welcome">
      <div class="welcome-ornament">⌂</div>
      <h1>Добро пожаловать в <em>ESTA Realty</em></h1>
      <p>Ваш персональный AI‑консьерж по недвижимости. Помогу найти идеальный объект, рассчитать ипотеку, оформить сделку.</p>
      <div class="welcome-chips">
        <button class="chip" onclick="sendQuick('Хочу купить квартиру до $60 000')">🏠 Купить квартиру</button>
        <button class="chip" onclick="sendQuick('Снять жильё на длительный срок')">🔑 Снять жильё</button>
        <button class="chip" onclick="sendQuick('Оценить мою квартиру')">💎 Оценить объект</button>
        <button class="chip" onclick="sendQuick('Инвестиции в недвижимость — с чего начать?')">📈 Инвестировать</button>
        <button class="chip" onclick="sendQuick('Как проходит сделка купли-продажи?')">📋 Процесс сделки</button>
      </div>
    </div>`;
}

function formatText(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^### (.*)/gm, '<strong style="font-size:15px;color:var(--gold-light)">$1</strong>')
    .replace(/^## (.*)/gm, '<strong style="font-size:16px;color:var(--gold-light)">$1</strong>')
    .replace(/^- (.*)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, (m) => `<ul>${m}</ul>`)
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}

async function sendMessage() {
  if (isLoading) return;
  const input = document.getElementById('userInput');
  const text = input.value.trim();
  if (!text) return;

  // Hide welcome
  const welcome = document.getElementById('welcome');
  if (welcome) welcome.style.display = 'none';

  input.value = '';
  input.style.height = 'auto';

  // Add user message
  addMsg('user', text);
  history.push({ role: 'user', content: text });

  // Show typing
  isLoading = true;
  document.getElementById('sendBtn').disabled = true;
  const typingId = addTyping();

  try {
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1000,
        system: SYSTEM_PROMPT,
        messages: history
      })
    });

    const data = await res.json();
    removeTyping(typingId);

    const reply = data.content?.[0]?.text || 'Извините, не удалось получить ответ. Попробуйте снова.';
    history.push({ role: 'assistant', content: reply });
    addMsg('bot', reply);

  } catch (err) {
    removeTyping(typingId);
    addMsg('bot', '⚠️ Ошибка соединения. Пожалуйста, попробуйте ещё раз или свяжитесь с агентом напрямую:\n\n📞 +7 (533) 12-34-56\n💬 @esta_realty_bot');
  }

  isLoading = false;
  document.getElementById('sendBtn').disabled = false;
  input.focus();
}

function addMsg(role, text) {
  const msgs = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = `msg ${role}`;

  const avatar = role === 'bot' ? '🏛' : '👤';
  div.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-bubble">${formatText(text)}</div>
  `;

  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div;
}

let typingCounter = 0;
function addTyping() {
  const id = ++typingCounter;
  const msgs = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg bot';
  div.id = `typing-${id}`;
  div.innerHTML = `
    <div class="msg-avatar">🏛</div>
    <div class="typing"><span></span><span></span><span></span></div>
  `;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(`typing-${id}`);
  if (el) el.remove();
}
</script>
</body>
</html>
