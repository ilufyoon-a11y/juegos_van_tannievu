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
    return "Juegos Activos"

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- 2. VARIABLES GLOBALES Y DICCONARIOS ---
# 📸 BANCO DE IMÁGENES FIJAS Y GIFS (¡Enlaces directos y limpios! 💅)
GIF_BIENVENIDA = "https://i.postimg.cc/T1jPgpDX/upscalemedia-transformed-(3).jpg"
GIF_INFO       = "https://i.postimg.cc/9XgrQHCd/upscalemedia-transformed-(1).jpg"
GIF_AHORCADO   = "https://i.postimg.cc/6qg3jBTv/1000004761.jpg"
FOTO_BOMBA     = "https://i.postimg.cc/ryb94Wgj/1000004755.jpg"
GIF_RATONES    = "https://i.postimg.cc/wMmHBLTM/1000004766.jpg"
GIF_RITMOAGO   = "https://i.postimg.cc/CMXk6g3n/upscalemedia-transformed.jpg"
GIF_ERROR      = "https://i.postimg.cc/G38XXrMW/Airbrush-IMAGE-ENHANCER-1779170852039-1779170852039.jpg"
GIF_OFFVAN     = "https://i.postimg.cc/mZ7k066k/upscalemedia-transformed-(2).jpg"

sesión = {}            # Ahorcado
esperando_palabra = {} # Ahorcado (Privado)

sesión_bomba = {
    "jugadores": [], "bomba_en": None, "bomba_emoji": None, "activa": False, "tarea_bomba": None, "mensaje_id": None
}

sesión_ratones = {
    "jugadores": [], "sobrevivientes": [], "esperando_click": [], "activa": False, "mensaje_id": None
}

sesión_stop = {
    "jugadores": [],        # Lista de inscritos
    "sobrevivientes": [],   # IDs de los que siguen vivos
    "turno_index": 0,       # Quién está jugando ahorita
    "palabras_dichas": [],  # Lista para que NO se repitan
    "letra_actual": "",
    "categoria_actual": "",
    "activa": False,
    "timer_task": None      # Control del reloj por turno
}

# 🎨 NUEVO DICCIONARIO VACÍO PARA EL JUEGO DEL DIBUJO
sesión_pictionary = {
    "activa": False,
    "palabra_correcta": None,
    "dibujante_id": None,
    "dibujante_name": None
}

# Banco de palabras secretas para el Pictionary
PALABRAS_PICTIONARY = [
    "shooky", "chimmy", "cooky", "tata", "mang", "rj", "koya", "van", 
    "microfono", "guitarra", "gato", "cafe", "piano", "army bomb"
]

CATEGORIAS_STOP = ["NOMBRE", "JUEGOS", "APELLIDO", "FRUTA O VERDURA ", "PAÍS O CIUDAD", "ANIMAL", "COLOR", "OBJETO", "PROFESIÓN  U OFICIO", "CANTANTE O BANDA", "COMIDA", "PELICULA O SERIE", "FAMOSO"]
EMOJIS_BOMBA = ["🦊", "🥑", "🐱", "🐸", "🐼", "🌶️", "👻", "👽", "🤖", "🦄", "👑", "🍕", "🎈", "🔮", "🦈", "🐥", "🐻", "🦖"]

# --- 3. AUXILIARES (AHORCADO) ---
def dibujar_pantalla_ahorcado(chat_id):
    datos = sesión[chat_id]
    palabra = datos["palabra_secreta"]
    adivinadas = datos["letras_adivinadas"]
    
    resultado = []
    for letra in palabra:
        if letra.lower() in adivinadas:
            resultado.append(letra + " ")
        elif letra == " ":
            resultado.append("  ")
        else:
            resultado.append("_ ")
            
    return "".join(resultado).strip()

# ₊˚ ✧ ‿︵‿୨୧‿︵‿ ✧ ₊˚ COMANDO START ₊˚ ✧ ‿︵‿୨୧‿︵‿ ✧ ₊˚
async def start_bienvenida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_animation(
        animation = GIF_BIENVENIDA,
        caption = "── .✦ Muchas gracias por ayudarme a testear mis codigos hechos con las patas, lo aprecio mucho, muack"
    )

# --- 4. COMANDO MENÚ PRINCIPAL ---
async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(
        photo = GIF_INFO,
        caption = (
            " ˗ˏˋ ꒰ LISTA DE COMANDOS INTRODUCIDOS ꒱ ˎˊ˗\n\n"
            "1. EL AHORCADO \n"
            "⤷ /ahorcado ⇢ Inicia el juego, crea una ronda y les permite a los demas unirse \n"
            "⤷ /start_ahorcado - Se elige a la persona que definirá la palabra para inicar el juego\n\n"
            "2. LA BOMBA \n"
            "⤷ /bomba ⇢ Inicia el juego, crea una ronda y les permite a los demas unirse\n"
            "⤷ /start_bomba - Encender la mecha\n\n"
            "3. RATONES \n"
            "⤷ /ratones ⇢ Inicia el juego, crea una ronda y les permite a los demas unirse\n"
            "⤷ /start_ratones ⇢ Se crea el tablero \n\n"
            "4. RITMO A GO-GO \n"
            "⤷ /stop ⇢ Alistarse para el la partida\n"
            "⤷ /start_stop ⇢ Lanza la letra, categoría e iniciar turnos\n\n"
            "5. PICTIONARY TRUCHO \n"
            "⤷ /garabato ⇢ Te da una palabra al azar por privado para que la dibujes y el grupo adivine\n"
        )
    )

# --- 5. JUEGO 1: AHORCADO ---
async def unirse_ahorcado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in sesión: 
        sesión[chat_id] = {"jugadores": [], "activa": False}
    else:
        sesión[chat_id]["activa"] = False
        sesión[chat_id]["jugadores"] = []
        
    boton = InlineKeyboardButton("UNIRSE", callback_data="unirme_click")
    await update.message.reply_photo(
        photo = GIF_AHORCADO,
        caption = "¡Juguemos al Ahorcado! Por favor presiona el boton para unirte:", 
        reply_markup=InlineKeyboardMarkup([[boton]])
    )

async def iniciar_ahorcado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in sesión or len(sesión[chat_id]["jugadores"]) < 2:
        await update.message.reply_animation(
            animation = GIF_ERROR,
            caption = "Se necesitan minimo 2 personas para jugar. De tratarse un error por favor vuelve a inciar el juego"
        )
        return 
        
    candidatos = list(sesión[chat_id]["jugadores"])
    ultimo_mod = sesión[chat_id].get("ultimo_moderador_id")
    if ultimo_mod and len(candidatos) > 1:
        filtrados = [j for j in candidatos if j["id"] != ultimo_mod]
        if filtrados:
            moderador = random.choice(filtrados)
        else:
            moderador = random.choice(candidatos)
    else:
        moderador = random.choice(candidatos)
    
    sesión[chat_id]["jugadores"].remove(moderador)
    sesión[chat_id].update({
        "moderador_id": moderador["id"], 
        "ultimo_moderador_id": moderador["id"], 
        "activa": True
    })
    
    esperando_palabra[moderador["id"]] = chat_id
    await update.message.reply_text(f"¡Iniciado! Moderador elegido: {moderador['name']}. Pásame la palabra al privado para poder iniciar el juego.")

# --- 6. JUEGO 2: LA BOMBA ---
async def unirse_bomba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sesión_bomba["jugadores"] = []
    sesión_bomba["activa"] = False
    boton = InlineKeyboardButton("ENTRAR AL CAMPO", callback_data="unirme_bomba_click")
    # Parcheado: Sin URL() y directo a reply_photo para que renderice en grande 💅
    await update.message.reply_photo(
        photo = FOTO_BOMBA,
        caption = "¡Juguemos a la Bomba! Por favor presiona el boton para unirte:", 
        reply_markup=InlineKeyboardMarkup([[boton]])
    )

async def iniciar_bomba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(sesión_bomba["jugadores"]) < 2:
        await update.message.reply_animation(
            animation = GIF_ERROR,
            caption = "Se necesitan minimo 2 personas para jugar. De tratarse un error por favor vuelve a inciar el juego"
        )
        return
    
    sesión_bomba["activa"] = True
    primer_jugador = random.choice(sesión_bomba["jugadores"])
    sesión_bomba["bomba_en"] = primer_jugador["id"]
    sesión_bomba["bomba_emoji"] = primer_jugador["emoji"]
    
    await update.message.reply_text(f"¡LA BOMBA ESTÁ ENCENDIDA!\n\nHa caído en manos de un jugador incógnito: {primer_jugador['emoji']}")
    sesión_bomba["tarea_bomba"] = asyncio.create_task(cuenta_regresiva_bomba(chat_id, context))

async def cuenta_regresiva_bomba(chat_id, context):
    tiempo_explotar = random.randint(15, 35) 
    
    botones = []
    for jugador in sesión_bomba["jugadores"]:
        if jugador["id"] != sesión_bomba["bomba_en"]: 
            botones.append([InlineKeyboardButton(f"Lanzar a {jugador['emoji']}", callback_data=f"pasar_a_{jugador['id']}")])
    
    mensaje_bomba = await context.bot.send_message(
        chat_id=chat_id, 
        text=f"¡La mecha fue encendida!\n\nLa tiene el jugador: {sesión_bomba['bomba_emoji']}\n¡Nadie sabe quién es! Elige un emoji para deshacerte de ella rápido:", 
        reply_markup=InlineKeyboardMarkup(botones),
    )
    
    sesión_bomba["mensaje_id"] = mensaje_bomba.message_id
    await asyncio.sleep(tiempo_explotar)
    
    if sesión_bomba["activa"]:
        sesión_bomba["activa"] = False
        perdedor_id = sesión_bomba["bomba_en"]
        perdedor = next(j for j in sesión_bomba["jugadores"] if j['id'] == perdedor_id)
        
        texto_final = f"¡¡¡¡BOOOOOOM!!!! \n\nLa bomba explotó en manos de {perdedor['name']} y quedó hecho cenizas."
        
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=sesión_bomba["mensaje_id"], text=texto_final)
        except:
            await context.bot.send_message(chat_id=chat_id, text=texto_final)

# --- 7. JUEGO 3: RATONES BATTLE ROYALE (3x3) ---
async def unirse_ratones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sesión_ratones["jugadores"] = []
    sesión_ratones["sobrevivientes"] = []
    sesión_ratones["activa"] = False
    boton = InlineKeyboardButton(" UNIRSE ", callback_data="unirme_ratones_click")
    await update.message.reply_photo(
        photo = GIF_RATONES,
        caption = "¡Golpea al ratón! \n¡El último en aplastarlo en cada ronda queda fuera!",
        reply_markup=InlineKeyboardMarkup([[boton]])
    )

async def iniciar_ratones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(sesión_ratones["jugadores"]) < 2:
        await update.message.reply_photo(
            photo = GIF_ERROR,
            caption = "Se necesitan minimo 2 personas para jugar. De tratarse un error por favor vuelve a inciar el juego"
        )
        return

    sesión_ratones["activa"] = True
    sesión_ratones["sobrevivientes"] = [j["id"] for j in sesión_ratones["jugadores"]]
    await update.message.reply_text("¡Apareciendo tablero! Atentos...")
    asyncio.create_task(rondas_battle_royale(chat_id, context))

async def rondas_battle_royale(chat_id, context):
    ronda = 1
    while sesión_ratones["activa"] and len(sesión_ratones["sobrevivientes"]) > 1:
        await asyncio.sleep(random.randint(3, 10))
        vivos = [next(j['name'] for j in sesión_ratones["jugadores"] if j['id'] == uid) for uid in sesión_ratones["sobrevivientes"]]
        await context.bot.send_message(chat_id=chat_id, text=f" RONDA {ronda}\nVivos: {', '.join(vivos)}")
        await asyncio.sleep(4)

        botones = [[InlineKeyboardButton("🕳️", callback_data="raton_fallo") for _ in range(3)] for _ in range(3)]
        botones[random.randint(0, 2)][random.randint(0, 2)] = InlineKeyboardButton("🐭", callback_data="raton_salvado")
        sesión_ratones["esperando_click"] = list(sesión_ratones["sobrevivientes"])
        
        sesión_ratones["mensaje_id"] = await context.bot.send_message(
            chat_id=chat_id, text="¡APARECIÓ EL RATÓN! ¡ATRAPALO!", reply_markup=InlineKeyboardMarkup(botones)
        )

        limite = 5.0
        while limite > 0 and len(sesión_ratones["esperando_click"]) > 1:
            await asyncio.sleep(0.5)
            limite -= 0.5

        try: await context.bot.delete_message(chat_id=chat_id, message_id=sesión_ratones["mensaje_id"].message_id)
        except: pass

        if len(sesión_ratones["esperando_click"]) > 0:
            lento_id = sesión_ratones["esperando_click"][-1]
            lento_name = next(j['name'] for j in sesión_ratones["jugadores"] if j['id'] == lento_id)
            sesión_ratones["sobrevivientes"].remove(lento_id)
            await context.bot.send_message(chat_id=chat_id, text=f" ¡{lento_name} fue muy lento! El ratón escapó. ELIMINADO.")
        ronda += 1

    sesión_ratones["activa"] = False
    if len(sesión_ratones["sobrevivientes"]) == 1:
        ganador_name = next(j['name'] for j in sesión_ratones["jugadores"] if j['id'] == sesión_ratones["sobrevivientes"][0])
        await context.bot.send_message(chat_id=chat_id, text=f"¡Termino la plaga de ratones!\n\nFelicidades {ganador_name}.")

# --- 8. JUEGO 4: RITMO A GO-GO ---
async def unirse_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sesión_stop["jugadores"] = []
    sesión_stop["activa"] = False
    boton = InlineKeyboardButton("UNIRME", callback_data="unirme_stop_click")
    await update.message.reply_photo(
        photo = GIF_RITMOAGO,
        caption = "¡Juguemos al Ritmo AGO-GO! Por favor, presiona el boton para unirte a la partida", 
        reply_markup=InlineKeyboardMarkup([[boton]])
    )

async def iniciar_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(sesión_stop["jugadores"]) < 2:
        await update.message.reply_photo(
            photo = GIF_ERROR,
            caption = "Se necesitan minimo 2 personas para jugar. De tratarse un error por favor vuelve a inciar el juego"
        )
        return
    
    sesión_stop["activa"] = True
    sesión_stop["sobrevivientes"] = [j["id"] for j in sesión_stop["jugadores"]]
    sesión_stop["palabras_dichas"] = []
    sesión_stop["turno_index"] = 0
    sesión_stop["letra_actual"] = random.choice("ABCDEFGJLMNOPRSTU")
    sesión_stop["categoria_actual"] = random.choice(CATEGORIAS_STOP)
    
    await update.message.reply_text(
        f"¡RITMO AGO-GO, DIGA USTED {sesión_stop['categoria_actual']} CON LA LETRA {sesión_stop['letra_actual']}\n\n¡Atentos a su turno!", 
    )
    await asyncio.sleep(3)
    await lanzar_turno_stop(chat_id, context)

async def lanzar_turno_stop(chat_id, context):
    if not sesión_stop["activa"]: return

    if len(sesión_stop["sobrevivientes"]) == 1:
        sesión_stop["activa"] = False
        ganador_name = next(j['name'] for j in sesión_stop["jugadores"] if j['id'] == sesión_stop["sobrevivientes"][0])
        await context.bot.send_message(chat_id=chat_id, text=f"¡{ganador_name} ganó el Ritmo A Go-Go!")
        return

    actual_id = sesión_stop["sobrevivientes"][sesión_stop["turno_index"]]
    actual_name = next(j['name'] for j in sesión_stop["jugadores"] if j['id'] == actual_id)

    await context.bot.send_message(
        chat_id=chat_id, 
        text=f"Turno de: {actual_name} ¡Escribe ya! (Tienes 12 segundos)"
    )

    if sesión_stop["timer_task"]: 
        sesión_stop["timer_task"].cancel()
    sesión_stop["timer_task"] = asyncio.create_task(timer_jugador_stop(chat_id, actual_id, actual_name, context))

async def timer_jugador_stop(chat_id, jugador_id, name, context):
    await asyncio.sleep(12)
    if sesión_stop["activa"] and sesión_stop["sobrevivientes"][sesión_stop["turno_index"]] == jugador_id:
        sesión_stop["sobrevivientes"].remove(jugador_id)
        await context.bot.send_message(chat_id=chat_id, text=f"⏳ ¡{name} no respondió a tiempo, eliminado por lento. 💀")
        
        if sesión_stop["turno_index"] >= len(sesión_stop["sobrevivientes"]):
            sesión_stop["turno_index"] = 0
        
        await lanzar_turno_stop(chat_id, context)

# --- 8.5 JUEGO 5: PICTIONARY TRUCHO (TU NUEVA IDEA) 🎨 ---
async def iniciar_pictionary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if sesión_pictionary["activa"]:
        await update.message.reply_text(f"¡Ya hay un garabato activo! Adivinen el de {sesión_pictionary['dibujante_name']} primero. 🤫")
        return

    palabra_elegida = random.choice(PALABRAS_PICTIONARY)
    
    sesión_pictionary.update({
        "activa": True,
        "palabra_correcta": palabra_elegida.lower(),
        "dibujante_id": user.id,
        "dibujante_name": user.first_name
    })

    await update.message.reply_text(
        f"🎨 *¡PICTIONARY TRUCHO INICIADO!* 🎨\n\n"
        f"El artista asignado es *{user.first_name}*.\n"
        f"Te acabo de mandar tu palabra secreta al privado. ¡Dibújala feo y manda la foto al grupo!"
    )

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=f"🤫 Tu palabra secreta es: *{palabra_elegida.upper()}*.\n\nHaz un garabato rápido en tu cel, guárdalo como imagen y envíalo a este grupo para que tus amigos adivinen."
        )
    except:
        await update.message.reply_text("❌ No pude mandarte un mensaje privado. Por favor, inicia un chat conmigo primero dándole a /start en mi privado.")

# --- 9. MANEJADOR DE CALLBACKS (BOTONES) ---
async def manejar_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat_id = query.message.chat.id
    await query.answer()

    # Callbacks Ahorcado
    if query.data == "unirme_click":
        if chat_id not in sesión: 
            sesión[chat_id] = {"jugadores": [], "activa": False}
        if not any(j['id'] == user.id for j in sesión[chat_id]["jugadores"]):
            sesión[chat_id]["jugadores"].append({"id": user.id, "name": user.first_name})
            await query.message.reply_text(f"{user.first_name} se unió a la ronda.")

    # Callbacks Bomba
    elif query.data == "unirme_bomba_click":
        if sesión_bomba["activa"]: 
            await query.message.reply_text(f"❌ {user.first_name}, ¡la partida ya empezó! Espera la otra ronda.")
            return
        if not any(j['id'] == user.id for j in sesión_bomba["jugadores"]):
            emojis_usados = [j["emoji"] for j in sesión_bomba["jugadores"]]
            emojis_disponibles = [e for e in EMOJIS_BOMBA if e not in emojis_usados]
            emoji_asignado = random.choice(emojis_disponibles) if emojis_disponibles else random.choice(EMOJIS_BOMBA)
            
            sesión_bomba["jugadores"].append({"id": user.id, "name": user.first_name, "emoji": emoji_asignado})
            await query.message.reply_text(f"💣 {user.first_name} entró de incógnito al campo.")

    elif query.data.startswith("pasar_a_"):
        if not sesión_bomba["activa"] or user.id != sesión_bomba["bomba_en"]: 
            return
        
        nuevo_id = int(query.data.replace("pasar_a_", ""))
        sesión_bomba["bomba_en"] = nuevo_id
        
        nuevo_jugador = next(j for j in sesión_bomba["jugadores"] if j['id'] == nuevo_id)
        user_jugador = next(j for j in sesión_bomba["jugadores"] if j['id'] == user.id)
        
        sesión_bomba["bomba_emoji"] = nuevo_jugador["emoji"]
        
        nuevos_botones = []
        for jugador in sesión_bomba["jugadores"]:
            if jugador["id"] != nuevo_id:
                nuevos_botones.append([InlineKeyboardButton(f"Lanzar a {jugador['emoji']}", callback_data=f"pasar_a_{jugador['id']}")])
        
        await query.message.edit_text(
            text=f"¡{user_jugador['emoji']} se salvó de milagro!\n\n💣 ¡Ahora la tiene {nuevo_jugador['emoji']}!\n¡Rápido, elige a qué emoji mandársela!",
            reply_markup=InlineKeyboardMarkup(nuevos_botones)
        )

    # Callbacks Ratones
    elif query.data == "unirme_ratones_click":
        if not any(j['id'] == user.id for j in sesión_ratones["jugadores"]):
            sesión_ratones["jugadores"].append({"id": user.id, "name": user.first_name})
            await query.message.reply_text(f"{user.first_name} entró a la caceria.")
    elif query.data == "raton_salvado":
        if sesión_ratones["activa"] and user.id in sesión_ratones["esperando_click"]:
            sesión_ratones["esperando_click"].remove(user.id)
            await query.message.reply_text(f"¡{user.first_name} logró aplastar al ratón!")
    elif query.data == "raton_fallo":
        if user.id in sesión_ratones["esperando_click"]:
            await query.message.reply_text(f"¡{user.first_name} le dio a un hueco vacío y el ratón escapo!.")

    # Callbacks STOP
    elif query.data == "unirme_stop_click":
        if not any(j['id'] == user.id for j in sesión_stop["jugadores"]):
            sesión_stop["jugadores"].append({"id": user.id, "name": user.first_name})
            await query.message.reply_text(f"{user.first_name} está listo para jugar.")

# --- 10. MANEJADOR DE MENSAJES (TEXTO) ---
async def manejar_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_type = update.effective_chat.type
    chat_id = update.effective_chat.id
    texto = update.message.text.strip() if update.message.text else ""
    
    if not texto:
        return

    # Setup Ahorcado por privado
    if chat_type == "private" and user_id in esperando_palabra:
        gid = esperando_palabra[user_id]
        
        sesión[gid].update({
            "palabra_secreta": texto.lower(), 
            "letras_adivinadas": [], 
            "jugadores_vidas": {}
        })
        del esperando_palabra[user_id]
        
        await update.message.reply_text("¡Palabra guardada! Vuelve al grupo.")
        guiones = " ".join(["_" if c != " " else "  " for c in texto])
        await context.bot.send_message(chat_id=gid, text=f"¡El moderador ya eligió!\nPalabra: '{guiones}'")
        return

    # Escucha del juego Pictionary en el Grupo 🎯
    if sesión_pictionary.get("activa") and chat_type != "private" and not texto.startswith("/"):
        if texto.lower() == sesión_pictionary["palabra_correcta"]:
            if user_id == sesión_pictionary["dibujante_id"]:
                await update.message.reply_text("¡Oye! Tú eres el dibujante, no hagas trampa soplándote a ti mismo. 🧐")
                return
            
            sesión_pictionary["activa"] = False
            palabra_ganadora = sesión_pictionary["palabra_correcta"].upper()
            await update.message.reply_text(
                f"🏆 *¡TENEMOS UN ADIVINADOR EXPERTO!* 🏆\n\n"
                f"*{user_name}* descifró el garabato de {sesión_pictionary['dibujante_name']}.\n"
                f"¡La palabra era: *{palabra_ganadora}*! 🥳🎨"
            )
            return

    # Escucha del juego Ahorcado en el Grupo 🎯
    if chat_id in sesión and sesión[chat_id].get("activa") and "palabra_secreta" in sesión[chat_id]:
        if len(texto) == 1 and texto.isalpha():
            if user_id == sesión[chat_id].get("moderador_id"):
                await update.message.reply_text("¡Oye! Tú eres la moderadora, no puedes jugar esta ronda.")
                return
                
            datos = sesión[chat_id]
            if user_id not in datos["jugadores_vidas"]: 
                datos["jugadores_vidas"][user_id] = 6
                
            if datos["jugadores_vidas"][user_id] <= 0: 
                await update.message.reply_text(f"❌ {user_name}, ya no tienes intentos en esta ronda.")
                return

            letra_ingresada = texto.lower()

            if letra_ingresada in datos["palabra_secreta"]:
                if letra_ingresada not in datos["letras_adivinadas"]: 
                    datos["letras_adivinadas"].append(letra_ingresada)
            else:
                datos["jugadores_vidas"][user_id] -= 1

            tablero = dibujar_pantalla_ahorcado(chat_id)
            await update.message.reply_text(
                f"Palabra: '{tablero}'\n"
                f"Intentos restantes de {user_name}: {datos['jugadores_vidas'][user_id]}"
            )
            
            if "_" not in tablero.replace(" ", ""):
                await update.message.reply_text(f"¡VICTORIA DE {user_name}! 🥳 La palabra era: {datos['palabra_secreta'].upper()}")
                datos["activa"] = False
            return

    # Escucha de Ritmo A Go-Go
    if sesión_stop.get("activa") and texto and not update.message.text.startswith("/"):
        actual_id = sesión_stop["sobrevivientes"][sesión_stop["turno_index"]]
        if user_id == actual_id:
            if sesión_stop["timer_task"]: 
                sesión_stop["timer_task"].cancel()

            palabra_limpia = texto.lower()

            if palabra_limpia in sesión_stop["palabras_dichas"]:
                sesión_stop["sobrevivientes"].remove(user_id)
                await update.message.reply_text(f"¡YA LA DIJERON! '{texto}' se repitió. {user_name} ELIMINADO")
            elif not texto.upper().startswith(sesión_stop["letra_actual"].upper()):
                sesión_stop["sobrevivientes"].remove(user_id)
                await update.message.reply_text(f"Tenía que empezar con {sesión_stop['letra_actual']}. {user_name} ELIMINADO")
            else:
                sesión_stop["palabras_dichas"].append(palabra_limpia)
                await update.message.reply_text(f"¡Bien! '{texto}' anotada.")
                sesión_stop["turno_index"] += 1

            if sesión_stop["turno_index"] >= len(sesión_stop["sobrevivientes"]):
                sesión_stop["turno_index"] = 0

            await lanzar_turno_stop(chat_id, context)
            return

# --- COMANDO DE APAGADO GENERAL ---
async def detener_juegos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # 1. 🎯 APAGÓN TOTAL AL AHORCADO
    if chat_id in sesión:
        sesión[chat_id]["activa"] = False
        sesión[chat_id]["jugadores"] = []
        if "palabra_secreta" in sesión[chat_id]:
            del sesión[chat_id]["palabra_secreta"]
            
    # 2. 💣 APAGÓN TOTAL A LA BOMBA
    sesión_bomba["activa"] = False
    sesión_bomba["jugadores"] = []
    if sesión_bomba.get("tarea_bomba"):
        try: sesión_bomba["tarea_bomba"].cancel()
        except: pass

    # 3. 🐭 APAGÓN TOTAL A LOS RATONES
    sesión_ratones["activa"] = False
    sesión_ratones["jugadores"] = []
    sesión_ratones["sobrevivientes"] = []
    sesión_ratones["esperando_click"] = []

    # 4. 🎤 APAGÓN TOTAL A RITMO A GO-GO (STOP)
    sesión_stop["activa"] = False
    sesión_stop["jugadores"] = []
    sesión_stop["sobrevivientes"] = []
    sesión_stop["palabras_dichas"] = []
    if sesión_stop.get("timer_task"):
        try: sesión_stop["timer_task"].cancel()
        except: pass

    # 5. 🎨 APAGÓN TOTAL AL PICTIONARY
    sesión_pictionary["activa"] = False
    sesión_pictionary["palabra_correcta"] = None
    sesión_pictionary["dibujante_id"] = None

    await update.message.reply_text(
        f"¡CLOSE VAN! 💥\n\nSe cerraron todas las rondas existentes." 
    )

# --- 11. BLOQUE PRINCIPAL DE ARRANQUE ---
if __name__ == '__main__':
    TOKEN = os.getenv("TOKEN_TELEGRAM")
    if TOKEN:
        keep_alive()
        application = ApplicationBuilder().token(TOKEN).build()
        
        # MENÚ PRINCIPAL
        application.add_handler(CommandHandler("start", start_bienvenida))
        application.add_handler(CommandHandler("off_van", detener_juegos))

        # Handlers JUEGO 1: Ahorcado
        application.add_handler(CommandHandler("ahorcado", unirse_ahorcado))
        application.add_handler(CommandHandler("info", comandos))
        application.add_handler(CommandHandler("start_ahorcado", iniciar_ahorcado))
        
        # Handlers JUEGO 2: La Bomba
        application.add_handler(CommandHandler("bomba", unirse_bomba))
        application.add_handler(CommandHandler("start_bomba", iniciar_bomba))
        
        # Handlers JUEGO 3: Ratones 3x3
        application.add_handler(CommandHandler("ratones", unirse_ratones))
        application.add_handler(CommandHandler("start_ratones", iniciar_ratones))
        
        # Handlers JUEGO 4: Ritmo A Go-Go
        application.add_handler(CommandHandler("stop", unirse_stop))
        application.add_handler(CommandHandler("start_stop", iniciar_stop))
        
        # Handlers JUEGO 5: Pictionary Trucho 🎨
        application.add_handler(CommandHandler("garabato", iniciar_pictionary))
        
        # Callbacks y Mensajes globales
        application.add_handler(CallbackQueryHandler(manejar_botones))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensajes))
        
        print("SISTEMA FUNCIONANDO, PRUEBALO!")
        application.run_polling()
