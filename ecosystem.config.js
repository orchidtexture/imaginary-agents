// filepath: ecosystem.config.js
module.exports = {
  apps : [{
    name   : "telegram-bot",
    script : "imaginary_agents/tg_bots/telegram_agent_bot.py",
    interpreter: "python3",
    env: {
      "NODE_ENV": "production",
    },
    output: '/var/log/telegram_bot_out.log',
    error: '/var/log/telegram_bot_err.log',
  }]
}