import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Diccionarios globales
sesión = {}
esperando_palabra = {}

# --- FUNCIÓN AUXILIAR DE DIBUJO ---
def dibujar_pantalla_ahorcado(chat_id):
    datos = sesión[chat_id]
    palabra = datos["palabra_secreta"]
    adivinadas = datos["letras_adivinadas"]
    
    resultado = ""
    for letra in palabra:
        if letra in adivinadas:
            resultado += letra + " "
        elif letra == " ":
            resultado += "  "  # Espacio doble para separar palabras
        else:
            resultado += "_ "
    return resultado.strip()

# --- FUNCIONES DE COMANDO ---
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
        sesión[chat_id] = {"jugadores": [], "activa": False, "juego": "ahorcado"}
    
    if not any(j['id'] == user.id for j in sesión[chat_id]["jugadores"]):
        sesión[chat_id]["jugadores"].append({"id": user.id, "name": user.first_name})
        await query.message.reply_text(f"{user.first_name} se unió al juego ♡.")
    else:
        await query.message.reply_text(f"Ya estás adentro, {user.first_name}, no te preocupes!")

async def iniciar_ahorcado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in sesión or len(sesión[chat_id]["jugadores"]) < 2:
        await update.message.reply_text("Se necesitan mínimo 2 personas para jugar.")
        return 
        
    lista_jugadores = sesión[chat_id]["jugadores"]
    moderador = random.choice(lista_jugadores)
    
    sesión[chat_id]["moderador_id"] = moderador["id"]
    esperando_palabra[moderador["id"]] = chat_id
    sesión[chat_id]["activa"] = True

    await update.message.reply_text(
        f"¡Juego Iniciado! \n"
        f"El moderador elegido es: {moderador['name']} \n"
        f"Por favor, {moderador['name']}, envía tu palabra al privado del bot para iniciar la ronda."
    )

# --- MANEJADOR DE MENSAJES ---
async def manejar_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_type = update.effective_chat.type
    texto = update.message.text.upper() if update.message.text else ""
    
    # --- CASO A: PRIVADO (MODERADOR) ---
    if chat_type == "private" and user_id in esperando_palabra:
        grupo_id = esperando_palabra[user_id]
        sesión[grupo_id]["palabra_secreta"] = texto
        sesión[grupo_id]["letras_adivinadas"] = []
        sesión[grupo_id]["jugadores_vidas"] = {} 
        
        del esperando_palabra[user_id]
        await update.message.reply_text("¡Palabra guardada! Ya puedes volver al grupo!")
        
        tablero_inicial = ""
        for carac in texto:
            tablero_inicial += "  " if carac == " " else "_ "

        await context.bot.send_message(
            chat_id=grupo_id, 
            text=f"¡El moderador ya eligió!\n\nPalabra: `{tablero_inicial.strip()}`",
        )
        return

    # --- CASO B: GRUPO (ADIVINAR) ---
    chat_id = update.effective_chat.id
    if chat_id in sesión and sesión[chat_id].get("activa") and "palabra_secreta" in sesión[chat_id]:
        
        if len(texto) != 1 or not texto.isalpha():
            return
        
        if user_id == sesión[chat_id]["moderador_id"]:
            return

        datos = sesión[chat_id]
        if user_id not in datos["jugadores_vidas"]:
            datos["jugadores_vidas"][user_id] = 6
        
        if datos["jugadores_vidas"][user_id] <= 0:
            return 

        # Lógica de Acierto/Error
        es_acierto = texto in datos["palabra_secreta"]
        
        if es_acierto:
            if texto not in datos["letras_adivinadas"]:
                datos["letras_adivinadas"].append(texto)
            mensaje_feedback = f"¡Sii, la {texto} sí está!."
        else:
            datos["jugadores_vidas"][user_id] -= 1
            mensaje_feedback = f"Ay, la {texto} no está!."

        # Variables para el mensaje final
        vidas = datos["jugadores_vidas"][user_id]
        tablero = dibujar_pantalla_ahorcado(chat_id)
        barra = "❤️" * vidas + "♡" * (6 - vidas) # Barra de vida con emojis

        # Armado del mensaje como pediste
        respuesta = (
            f"Palabra: `{tablero}`\n"
            f"Intentos restantes: {vidas} {barra}\n"
            f"{mensaje_feedback}"
        )
        
        await update.message.reply_text(respuesta)
        
        # Condiciones finales
        if "_" not in tablero:
            await update.message.reply_text(f"✨ ¡VICTORIA! ✨\nLa palabra era: {datos['palabra_secreta']}")
            datos["activa"] = False
        elif vidas == 0:
            await update.message.reply_text(f"{user_name} ha sido eliminado del juego.")
