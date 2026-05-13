import random
import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- 1. DESPERTADOR PARA RENDER (FLASK) ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "Juegos mango- Activo"

def run_web():
    # Render usa el puerto 10000 por defecto, pero os.environ lo detecta
    port = int(os.environ.get('PORT', 10000))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- 2. VARIABLES GLOBALES ---
sesión = {}
esperando_palabra = {}

# --- 3. FUNCIONES AUXILIARES ---
def dibujar_pantalla_ahorcado(chat_id):
    datos = sesión[chat_id]
    palabra = datos["palabra_secreta"]
    adivinadas = datos["letras_adivinadas"]
    
    resultado = ""
    for letra in palabra:
        if letra in adivinadas:
            resultado += letra + " "
        elif letra == " ":
            resultado += "  "
        else:
            resultado += "_ "
    return resultado.strip()

# --- 4. FUNCIONES DE COMANDO ---
async def unirse_ahorcado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    boton_joinin = InlineKeyboardButton("꒦꒷ UNIRME ꒦꒷", callback_data="unirme_click")
    reply_markup = InlineKeyboardMarkup([[boton_joinin]])
    
    await update.message.reply_text(
        "¡Bienvenidos al juego del ahorcado! Por favor, presiona el botón para poder unirte:",
        reply_markup=reply_markup
    )

async def unirme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat.id
    user = query.from_user
    
    if chat_id not in sesión:
        sesión[chat_id] = {"jugadores": [], "activa": False}
    
    if not any(j['id'] == user.id for j in sesión[chat_id]["jugadores"]):
        sesión[chat_id]["jugadores"].append({"id": user.id, "name": user.first_name})
        await query.message.reply_text(f"{user.first_name} se unió al juego ♡.")
    else:
        await query.message.reply_text(f"Ya estás adentro, {user.first_name}!")

async def iniciar_ahorcado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in sesión or len(sesión[chat_id]["jugadores"]) < 2:
        await update.message.reply_text("Se necesitan mínimo 2 personas para jugar, causa.")
        return 
        
    lista_jugadores = sesión[chat_id]["jugadores"]
    moderador = random.choice(lista_jugadores)
    
    sesión[chat_id]["moderador_id"] = moderador["id"]
    esperando_palabra[moderador["id"]] = chat_id
    sesión[chat_id]["activa"] = True

    await update.message.reply_text(
        f"¡Juego Iniciado! 🚀\n"
        f"El moderador elegido es: {moderador['name']} \n"
        f"Por favor, {moderador['name']}, envía la palabra al privado del bot."
    )

# --- 5. MANEJADOR DE MENSAJES ---
async def manejar_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_type = update.effective_chat.type
    texto = update.message.text.upper() if update.message.text else ""
    
    # CASO A: PRIVADO (MODERADOR ELIGE PALABRA)
    if chat_type == "private" and user_id in esperando_palabra:
        grupo_id = esperando_palabra[user_id]
        sesión[grupo_id]["palabra_secreta"] = texto
        sesión[grupo_id]["letras_adivinadas"] = []
        sesión[grupo_id]["jugadores_vidas"] = {} 
        
        del esperando_palabra[user_id]
        await update.message.reply_text("¡Palabra guardada! Vuelve al grupo.")
        
        guiones = " ".join(["_" if c != " " else "  " for c in texto])
        await context.bot.send_message(
            chat_id=grupo_id, 
            text=f"¡El moderador ya eligió!\n\nPalabra: `{guiones}`",
            parse_mode="Markdown"
        )
        return

    # CASO B: GRUPO (ADIVINAR)
    chat_id = update.effective_chat.id
    if chat_id in sesión and sesión[chat_id].get("activa") and "palabra_secreta" in sesión[chat_id]:
        
        if len(texto) != 1 or not texto.isalpha() or user_id == sesión[chat_id]["moderador_id"]:
            return

        datos = sesión[chat_id]
        if user_id not in datos["jugadores_vidas"]:
            datos["jugadores_vidas"][user_id] = 6
        
        if datos["jugadores_vidas"][user_id] <= 0:
            return 

        if texto in datos["palabra_secreta"]:
            if texto not in datos["letras_adivinadas"]:
                datos["letras_adivinadas"].append(texto)
            feedback = f"¡Sii, la {texto} está!"
        else:
            datos["jugadores_vidas"][user_id] -= 1
            feedback = f"Ay, la {texto} no está."

        vidas = datos["jugadores_vidas"][user_id]
        tablero = dibujar_pantalla_ahorcado(chat_id)
        barra = "❤️" * vidas + "♡" * (6 - vidas)

        await update.message.reply_text(
            f"Palabra: `{tablero}`\n"
            f"Intentos: {vidas} {barra}\n"
            f"{feedback}",
            parse_mode="Markdown"
        )
        
        if "_" not in tablero:
            await update.message.reply_text(f"✨ ¡VICTORIA! {user_name} adivinó la última letra. ✨\nLa palabra era: **{datos['palabra_secreta']}**")
            datos["activa"] = False
        elif vidas == 0:
            await update.message.reply_text(f"💀 {user_name} ha sido eliminado.")

# --- 6. BLOQUE PRINCIPAL ---
if __name__ == '__main__':
    TOKEN = os.getenv("TOKEN_TELEGRAM")
    
    if not TOKEN:
        print("❌ Error: No se encontró el TOKEN_TELEGRAM")
    else:
        # Iniciar servidor web para que Render no se duerma
        keep_alive()
        
        # Crear la aplicación
        application = ApplicationBuilder().token(TOKEN).build()
    
        # Registrar Handlers
        application.add_handler(CommandHandler("ahorcado", unirse_ahorcado))
        application.add_handler(CommandHandler("start_ahorcado", iniciar_ahorcado))
        application.add_handler(CallbackQueryHandler(unirme, pattern="unirme_click"))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensajes))
        
        print("Bot encendido correctamente... 🚀")
        application.run_polling()
