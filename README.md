# ✈ Aviator Signal Bot — Void Partners

Bot do Telegram para disparo automático de sinais do Aviator.

---

## 📋 Estrutura

```
aviator-bot/
├── bot.py            → Código principal do bot
├── painel.html       → Painel web de controle
├── .env.example      → Template de configuração
├── requirements.txt  → Dependências Python
└── README.md
```

---

## 🚀 Instalação

### 1. Criar o Bot no Telegram

1. Abra o Telegram e procure por **@BotFather**
2. Envie `/newbot`
3. Escolha um nome (ex: `Aviator Void Sinais`)
4. Escolha um username (ex: `@void_aviator_bot`)
5. **Copie o token** que o BotFather enviar

### 2. Criar o Canal

1. Crie um canal no Telegram (ex: `@void_aviator_sinais`)
2. Adicione o bot ao canal como **administrador**
3. Dê permissão para o bot **postar mensagens**

### 3. Descobrir seu ID de Admin

1. Fale com [@userinfobot](https://t.me/userinfobot) no Telegram
2. Ele vai retornar seu `id` numérico

### 4. Configurar o .env

```bash
cp .env.example .env
nano .env
```

Preencha:
```
BOT_TOKEN=SEU_TOKEN_AQUI
CHANNEL_ID=@seu_canal
ADMIN_IDS=SEU_ID_AQUI
```

### 5. Instalar dependências

```bash
pip install -r requirements.txt
```

### 6. Rodar o bot

```bash
python bot.py
```

---

## 🎮 Comandos Disponíveis (Admin)

| Comando | Descrição |
|---------|-----------|
| `/start` | Mensagem de boas-vindas |
| `/disparar` | Dispara um sinal aleatório no canal |
| `/sinal 2.50` | Dispara sinal com multiplicador específico |
| `/status` | Mostra status do bot |

---

## ⏰ Sinais Automáticos

Por padrão, o bot envia sinais **a cada 15 minutos**.

Para alterar, edite no `bot.py`:
```python
schedule.every(15).minutes.do(scheduled_job)
```

Exemplos:
```python
schedule.every(30).minutes.do(scheduled_job)   # a cada 30 min
schedule.every().hour.at(":00").do(scheduled_job)  # de hora em hora
schedule.every().day.at("20:00").do(scheduled_job)  # às 20h todo dia
```

---

## 🖥 Painel Web

Abra o `painel.html` no navegador para:
- Disparar sinais manualmente
- Configurar multiplicador, confiança e entradas
- Ver log de disparos
- Controlar horários ativos

> O painel é local (HTML puro). Para integração real com o bot via API, precisaria de um servidor Flask/FastAPI.

---

## 🌐 Deploy (VPS/Servidor)

Para rodar 24/7 em um servidor:

```bash
# Instalar PM2 ou usar screen/tmux
pip install -r requirements.txt
python bot.py &

# Ou com systemd:
# Crie /etc/systemd/system/aviator-bot.service
```

---

## ⚠️ Aviso Legal

Este sistema é uma ferramenta de automação de comunicação.
Sempre inclua disclaimers de responsabilidade nos sinais.
Jogo deve ser apenas para maiores de 18 anos.
Cumpra com as regulamentações da Lei 14.790/23.
