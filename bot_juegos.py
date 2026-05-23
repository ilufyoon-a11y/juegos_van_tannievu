import random
import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# =====================================================================
# 1. DESPERTADOR PARA RENDER (FLASK)
# =====================================================================
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


# =====================================================================
# 2. VARIABLES GLOBALES Y DICCIONARIOS
# =====================================================================
GIF_BIENVENIDA = "https://i.postimg.cc/T1jPgpDX/upscalemedia-transformed-(3).jpg" 
GIF_INFO       = "https://i.postimg.cc/9XgrQHCd/upscalemedia-transformed-(1).jpg" 
GIF_AHORCADO   = "https://i.postimg.cc/6qg3jBTv/1000004761.jpg" 
GIF_SNOWBALL   = "https://i.postimg.cc/ryb94Wgj/1000004755.jpg" 
GIF_RATONES    = "https://i.postimg.cc/wMmHBLTM/1000004766.jpg" 
GIF_RITMOAGO   = "https://i.postimg.cc/CMXk6g3n/upscalemedia-transformed.jpg" 
GIF_ERROR      = "https://i.postimg.cc/G38XXrMW/Airbrush-IMAGE-ENHANCER-1779170852039-1779170852039.jpg" 
GIF_OFFVAN     = "https://i.postimg.cc/mZ7k066k/upscalemedia-transformed-(2).jpg" 
GIF_JITB       = "https://i.postimg.cc/fLqYbX2s/Airbrush-IMAGE-ENHANCER-1779302294635-1779302294635.jpg" 
GIF_ZOMBIE     = "https://i.postimg.cc/8PWQJWM1/1000004869.jpg" 
GIF_ENCUBRIDOR = "https://i.postimg.cc/QMmj1qZm/8a87226444e22cdd01aaff0060557a2b-(1).jpg"
GIF_CERO       = "https://i.postimg.cc/vH5TDfDZ/763aa3f517ca4e8b1b1ae10f55dfb556-(1).jpg"
GIF_LETRISTA   = "https://i.postimg.cc/Zndk78XB/Airbrush-IMAGE-ENHANCER-1779303536547-1779303536547.jpg"
GIF_RECHAZADO  = "https://i.postimg.cc/MTXZnXd8/1000005045.jpg"
GIF_COMANDOS   = "https://i.postimg.cc/6qjQHnqv/1000005043-(1).jpg"

sesión = {}            
esperando_palabra = {} 
esperando_elementos = {} 

sesión_bomba = {
    "jugadores": [], 
    "bomba_en": None, 
    "bomba_emoji": None, 
    "activa": False, 
    "tarea_bomba": None, 
    "mensaje_id": None
}

sesión_ratones = {
    "jugadores": [], 
    "sobrevivientes": [], 
    "esperando_click": [], 
    "activa": False, 
    "mensaje_id": None
}

sesión_stop = {
    "jugadores": [],       
    "sobrevivientes": [],  
    "turno_index": 0,       
    "palabras_dichas": [],  
    "letra_actual": "",
    "categoria_actual": "",
    "activa": False,
    "timer_task": None      
}

sesión_zombie = {
    "jugadores": [],        
    "activa": False,        
    "zombies": [],          
    "vivos": [],            
    "fase": None,           
    "votos": {},            
    "mensaje_voto_id": None 
}
esperando_mordida = {}     

sesión_jitb = {}

CATEGORIAS_STOP = ["𝗡𝗢𝗠𝗕𝗥𝗘", "𝗔𝗣𝗘𝗟𝗟𝗜𝗗𝗢", "𝗙𝗥𝗨𝗧𝗔 𝗢 𝗩𝗘𝗥𝗗𝗨𝗥𝗔", "𝗣𝗔𝗜𝗦 𝗢 𝗖𝗜𝗨𝗗𝗔𝗗", "𝗔𝗡𝗜𝗠𝗔𝗟", "𝗖𝗢𝗟𝗢𝗥", "𝗢𝗕𝗝𝗘𝗧𝗢", "𝗣𝗥𝗢𝗙𝗘𝗦𝗜𝗢́𝗡  𝗨 𝗢𝗙𝗜𝗖𝗜𝗢", "𝗖𝗔𝗡𝗧𝗔𝗡𝗧𝗘 𝗢 𝗕𝗔𝗡𝗗𝗔", "𝗖𝗢𝗠𝗜𝗗𝗔", "𝗣𝗘𝗟𝗜𝗖𝗨𝗟𝗔 𝗢 𝗦𝗘𝗥𝗜𝗘", "𝗙𝗔𝗠𝗢𝗦𝗢"]
EMOJIS_BOMBA = ["🦊", "🥑", "🐱", "🐸", "🐼", "🌶️", "👻", "👽", "🤖", "🦄", "👑", "🍕", "🎈", "🔮", "🦈", "🐥", "🐻", "🦖"]


# =====================================================================
# 3. AUXILIARES GENERALES
# =====================================================================
def dibujar_pantalla_ahorcado(chat_id):
    if chat_id not in sesión: return ""
    datos = sesión[chat_id]
    palabra = datos.get("palabra_secreta", "")
    adivinadas = datos.get("letras_adivinadas", [])
    
    resultado = []
    for letra in palabra:
        if letra.lower() in adivinadas:
            resultado.append(letra + " ")
        elif letra == " ":
            resultado.append("  ")
        else:
            resultado.append("_ ")
            
    return "".join(resultado).strip()

# COMANDO START
async def start_bienvenida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(
        photo = GIF_BIENVENIDA,
        caption = "\n\n🌸ㅤㅤ⪩⪩ㅤㅤ𝐁𝐢𝐞𝐧𝐯𝐞𝐧𝐢𝐝@ㅤㅤ!!ㅤㅤ☆ \n\n𝖵𝖺𝗇 𝖾𝗌 𝗎𝗇 𝖻𝗈𝗍 𝗊𝗎𝖾 𝗈𝖿𝗋𝖾𝖼𝖾 𝗎𝗇𝖺 𝗏𝖺𝗋𝗂𝖾𝖽𝖺𝖽 𝖽𝖾 𝗃𝗎𝖾𝗀𝗈𝗌, 𝖺𝗎𝗇 𝖾𝗌𝗍𝖺 𝖾𝗇 𝗉𝗋𝗈𝖼𝖾𝗌𝗈 𝖽𝖾 𝗉𝗋𝗎𝖾𝖻𝖺 𝖺𝗌𝗂 𝗊𝗎𝖾 𝗌𝗂𝖾𝗇𝗍𝖾𝗍𝖾 𝖾𝗇 𝗍𝗈𝗍𝖺𝗅 𝗅𝗂𝖻𝖾𝗋𝗍𝖺𝖽 𝖽𝖾 𝖼𝗈𝗆𝗎𝗇𝗂𝖼𝖺𝗋 𝖼𝗎𝖺𝗅𝗊𝗎𝗂𝖾𝗋 𝗊𝗎𝖾𝗃𝖺/𝗌𝗎𝗀𝖾𝗋𝖾𝗇𝖼𝗂𝖺 𝖾𝗇 𝖾𝗅 𝖼𝗁𝖺𝗍 𝖽𝖾𝗅 𝖼𝖺𝗇𝖺𝗅. \n\n𝖤𝗌𝗉𝖾𝗋𝖺𝗆𝗈𝗌 𝗊𝗎𝖾 𝗅𝗈𝗌 𝗃𝗎𝖾𝗀𝗈𝗌 𝖼𝗈𝗇𝗍𝖾𝗇𝗂𝖽𝗈𝗌 𝗌𝖾𝖺𝗇 𝖽𝖾 𝗌𝗎 𝖺𝗀𝗋𝖺𝖽𝗈! 💕"
    )

# INFO DE LOS JUEGOS 
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_photo(
        photo = GIF_INFO,
        caption = ("🐋    𖹭𖹭ㅤ𝗝𝗨𝗘𝗚𝗢𝗦 𝗗𝗜𝗦𝗣𝗢𝗡𝗜𝗕𝗟𝗘𝗦     ꒱꒱\n\n"
            "𝒊. 𝐀𝐡𝐨𝐫𝐜𝐚𝐝𝐨\n\n"
            "𝖤𝗅 𝗃𝗎𝖾𝗀𝗈 𝖼𝗅𝖺𝗌𝗂𝖼𝗈 𝗊𝗎𝖾 𝗍𝗈𝖽𝗈𝗌 𝖼𝗈𝗇𝗈𝖼𝖾𝗇\n\n"
            "𝒊𝒊. 𝐒𝐧𝐨𝐰𝐛𝐚𝐥𝐥\n\n"
            "𝖴𝗇𝖺 𝖻𝗈𝗅𝖺 𝖽𝖾 𝗇𝗂𝖾𝗏𝖾 𝖾𝗌𝗍𝖺 𝖻𝖺𝗃𝖺𝗇𝖽𝗈 𝖽𝖾𝗌𝖽𝖾 𝗎𝗇𝖺 𝖼𝗈𝗅𝗂𝗇𝖺 𝗒 𝗏𝖺 𝖽𝗂𝗋𝖾𝖼𝗍𝗈 𝗁𝖺𝖼𝗂𝖺 𝖺 𝗎𝗌𝗍𝖾𝖽𝖾𝗌. ¡𝖫𝖺𝗇𝗓𝖺𝗅𝖺 𝖺 𝗈𝗍𝗋𝗈 𝗈 𝗊𝗎𝖾𝖽𝖺 𝖺𝗉𝗅𝖺𝗌𝗍𝖺𝖽@!\n\n"
            "𝒊𝒊. 𝐑𝐚𝐭𝐨𝐧𝐞𝐬\n\n"
            "𝖴𝗇𝖺 𝗉𝗅𝖺𝗀𝖺 𝗌𝖾 𝗁𝖺 𝖽𝖾𝗌𝗁𝖺𝗍𝖺𝖽𝗈 𝗒 𝗅𝖺 𝗎𝗇𝗂𝖼𝖺 𝖿𝗈𝗋𝗆𝖺 𝖽𝖾 𝖽𝖾𝗌𝗁𝖺𝖼𝖾𝗋𝗌𝖾 𝖽𝖾 𝖾𝗅𝗅𝖺 𝖾𝗌 𝗀𝗈𝗅𝗉𝖾𝖺𝗇𝖽𝗈 𝖺 𝗅𝗈𝗌 𝗋𝖺𝗍𝗈𝗇𝖾𝗌\n\n"
            "𝒊𝒗. 𝐑𝐢𝐭𝐦𝐨 𝐀𝐠𝐨 𝐆𝐨\n\n"
            "𝖴𝗇𝖺 𝗏𝖺𝗋𝗂𝖺𝖼𝗂𝗈𝗇 𝖽𝖾 𝗌𝗍𝗈𝗉, 𝖽𝗈𝗇𝖽𝖾 𝖼𝖺𝖽𝖺 𝗎𝗇𝗈 𝖽𝖾𝖻𝖾 𝖽𝖾𝖼𝗂𝗋 𝗉𝖺𝗅𝖺𝖻𝗋𝖺𝗌 𝗋𝖾𝗅𝖺𝖼𝗂𝗈𝗇𝖺𝖽𝖺𝗌 𝖺 𝗅𝖺 𝖼𝖺𝗍𝖾𝗀𝗈𝗋𝗂𝖺 𝗌𝗂𝗇 𝗋𝖾𝗉𝖾𝗍𝗂𝗋 𝗅𝖺𝗌 𝖽𝗂𝖼𝗁𝖺𝗌 𝖺𝗇𝗍𝖾𝗋𝗂𝗈𝗋𝗆𝖾𝗇𝗍𝖾\n\n"
            "𝒗. 𝐖𝐡𝐚𝐭'𝐬 𝐢𝐧 𝐭𝐡𝐞 𝐛𝐨𝐱\n\n"
            "𝖨𝗇𝗌𝗉𝗂𝗋𝖺𝖽𝗈 𝖾𝗇 𝖵𝖺𝗋𝗂𝖾𝗍𝗒 𝖲𝗁𝗈𝗐𝗌 𝗈𝖿 𝖬𝖾𝗆𝗈𝗋𝗂𝖾𝗌: 𝖯𝖺𝗋𝗍 𝟣, 𝗍𝖾𝗇𝖽𝗋𝖺𝗇 𝗌𝗈𝗅𝗈 𝟧 𝗌𝖾𝗀𝗎𝗇𝖽𝗈𝗌 𝗉𝖺𝗋𝖺 𝗆𝖾𝗆𝗈𝗋𝗂𝗓𝖺𝗋 𝗅𝗈𝗌 𝗈𝖻𝗃𝖾𝗍𝗈𝗌 𝖽𝖾𝗇𝗍𝗋𝗈 𝖽𝖾 𝗅𝖺 𝖼𝖺𝗃𝖺. ¡𝖠 𝗆𝖺𝗒𝗈𝗋 𝗈𝖻𝗃𝖾𝗍𝗈𝗌 𝖺𝖽𝗂𝗏𝗂𝗇𝖺𝖽𝗈𝗌, 𝗆𝖺𝗒𝗈𝗋 𝗉𝗎𝗇𝗍𝖺𝗃𝖾!\n\n"
            "𝒗𝒊. 𝐙𝐨𝐦𝐛𝐢𝐞\n\n"
            "𝖴𝗇𝖺 𝖾𝗑𝖼𝗎𝗋𝗌𝗂𝗈𝗇 𝗌𝖾 𝗏𝗂𝗈 𝗂𝗇𝗍𝖾𝗋𝗋𝗎𝗆𝗉𝗂𝖽𝖺 𝗉𝗈𝗋 𝗎𝗇 𝗏𝗂𝗋𝗎𝗌 𝗓𝗈𝗆𝖻𝗂𝖾 𝗒 𝖽𝖾𝖻𝖾𝗇 𝖾𝗌𝗉𝖾𝗋𝖺𝗋 𝗁𝖺𝗌𝗍𝖺 𝗊𝗎𝖾 𝗅𝗈𝗌 𝗋𝖾𝗌𝖼𝖺𝗍𝖾𝗇, 𝗌𝗈𝗅𝗈 𝗌𝖾 𝗉𝗎𝖾𝖽𝖾𝗇 𝗋𝖾𝗌𝗀𝗎𝖺𝗋𝖽𝖺𝗋 𝖾𝗇 𝗎𝗇 𝖺𝗎𝗍𝗈𝖻𝗎𝗌, 𝗉𝖾𝗋𝗈 𝗎𝗇 𝗂𝗇𝖿𝖾𝖼𝗍𝖺𝖽𝗈 𝗌𝖾 𝖼𝗈𝗅𝗈 𝗒 𝖺𝗍𝖺𝖼𝖺 𝗉𝗈𝗋 𝗅𝖺𝗌 𝗇𝗈𝖼𝗁𝖾𝗌 𝖼𝗎𝖺𝗇𝖽𝗈 𝗅𝖺𝗌 𝗅𝗎𝖼𝖾𝗌 𝗌𝖾 𝖺𝗉𝖺𝗀𝖺𝗇 𝗉𝗈𝗋 𝗌𝖾𝗀𝗎𝗋𝗂𝖽𝖺𝖽 ¿𝖯𝗈𝖽𝗋𝖺𝗇 𝗌𝗈𝖻𝗋𝖾𝗏𝗂𝗏𝗂𝗋?\n\n" 

        )        
)

# INFO DE LOS COMANDOS 
async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(
        photo = GIF_COMANDOS,
        caption = ("🎡  𖹭𖹭 ㅤ𝗖𝗼𝗺𝗮𝗻𝗱𝗼𝘀 𝗱𝗶𝘀𝗽𝗼𝗻𝗶𝗯𝗹𝗲𝘀  ꒱꒱\n\n"
            "𝒊. 𝐀𝐡𝐨𝐫𝐜𝐚𝐝𝐨\n\n"
            "𝖢𝗈𝗆𝖺𝗇𝖽𝗈𝗌: /ahorcado, /start_ahorcado\n\n"
            "𝒊𝒊. 𝐒𝐧𝐨𝐰𝐛𝐚𝐥𝐥\n\n"
            "𝖢𝗈𝗆𝖺𝗇𝖽𝗈𝗌: /snowball, /start_snowball\n\n"
            "𝒊𝒊. 𝐑𝐚𝐭𝐨𝐧𝐞𝐬\n\n"
            "𝖢𝗈𝗆𝖺𝗇𝖽𝗈𝗌: /ratones, /start_ratones\n\n"
            "𝒊𝒗. 𝐑𝐢𝐭𝐦𝐨 𝐀𝐠𝐨 𝐆𝐨\n\n"
            "𝖢𝗈𝗆𝖺𝗇𝖽𝗈𝗌: /ritmo, /start_ritmo\n\n"
            "𝒗. 𝐖𝐡𝐚𝐭'𝐬 𝐢𝐧 𝐭𝐡𝐞 𝐛𝐨𝐱\n\n"
            "𝖢𝗈𝗆𝖺𝗇𝖽𝗈𝗌: /box, /start_box\n\n"
            "𝒗𝒊. 𝐙𝐨𝐦𝐛𝐢𝐞\n\n"
            "𝖢𝗈𝗆𝖺𝗇𝖽𝗈𝗌: /zombie, /start_zombie\n\n" 
            "𝖠𝗇𝗍𝖾𝗌 𝖽𝖾 𝗂𝗇𝗂𝖼𝗂𝖺𝗋 𝗎𝗇𝖺 𝗋𝗈𝗇𝖽𝖺 𝗇𝗎𝖾𝗏𝖺 𝗈 𝗁𝖺𝖻𝖾𝗋𝗌𝖾 𝗂𝗇𝗂𝖼𝗂𝖺𝖽𝗈 𝗆𝖺𝗌 𝖽𝖾 𝗎𝗇𝖺 𝗉𝗈𝗋 𝖾𝗊𝗎𝗂𝗏𝗈𝖼𝖺𝖼𝗂𝗈𝗇, 𝗉𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝖾𝗃𝖾𝖼𝗎𝗍𝖾 /off_van 𝗉𝖺𝗋𝖺 𝗋𝖾𝗌𝖾𝗍𝖾𝖺𝗋 𝖾𝗅 𝖼𝗈𝖽𝗂𝗀𝗈 𝗒 𝖾𝗏𝗂𝗍𝖺𝗋 𝖾𝗋𝗋𝗈𝗋𝖾𝗌"

        )
    )

# JUEGO 1: AHORCADO 
async def unirse_ahorcado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in sesión: 
        sesión[chat_id] = {"jugadores": [], "activa": False}
    else:
        sesión[chat_id]["activa"] = False
        sesión[chat_id]["jugadores"] = []
        
    boton = InlineKeyboardButton("੭੭ㅤㅤ𝐔𝐍𝐈𝐑𝐌𝐄ㅤㅤ!¡", callback_data="unirme_click")
    await update.message.reply_photo(
        photo = GIF_AHORCADO,
        caption = "\n\n ៹ ࣪  📝 ¡𝖩𝗎𝗀𝗎𝖾𝗆𝗈𝗌 𝖺𝗅 𝖺𝗁𝗈𝗋𝖼𝖺𝖽𝗈! 𝖯𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝗉𝗋𝖾𝗌𝗂𝗈𝗇𝖺 𝖾𝗅 𝖻𝗈𝗍𝗈𝗇 𝗉𝖺𝗋𝖺 𝗎𝗇𝗂𝗋𝗍𝖾 𝖺 𝗅𝖺 𝗉𝖺𝗋𝗍𝗂𝖽𝖺  ֪   𓂃",
        reply_markup=InlineKeyboardMarkup([[boton]])
    )

async def iniciar_ahorcado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in sesión or len(sesión[chat_id]["jugadores"]) < 2:
        await update.message.reply_photo(
            photo = GIF_ERROR,
            caption = "𝖲𝖾 𝗇𝖾𝖼𝖾𝗌𝗂𝗍𝖺𝗇 𝗆𝗂𝗇𝗂𝗆𝗈 𝟤 𝗉𝖾𝗋𝗌𝗈𝗇𝖺𝗌 𝗉𝖺𝗋𝖺 𝗃𝗎𝗀𝖺𝗋. 𝖣𝖾 𝗍𝗋𝖺𝗍𝖺𝗋𝗌𝖾 𝗎𝗇 𝖾𝗋𝗋𝗈𝗋, 𝗉𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝗏𝗎𝖾𝗅𝗏𝖾 𝖺 𝗂𝗇𝗂𝖼𝗂𝖺𝗋 𝖾𝗅 𝗃𝗎𝖾𝗀𝗈."
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
    await update.message.reply_text(f"˒˓  ¡𝖬𝗈𝖽𝖾𝗋𝖺𝖽𝗈𝗋 𝖾𝗅𝖾𝗀𝗂𝖽𝗈!. 𝖤𝗌𝗉𝖾𝗋𝖺𝗇𝖽𝗈 𝗊𝗎𝖾 𝗌𝖾 𝖺𝗌𝗂𝗀𝗇𝖾 𝗅𝖺 𝗉𝖺𝗅𝖺𝖻𝗋𝖺 𝗉𝖺𝗋𝖺 𝗉𝗈𝖽𝖾𝗋 𝗂𝗇𝗂𝖼𝗂𝖺𝗋 𝖾𝗅 𝗃𝗎𝖾𝗀𝗈  ᨦᨩ") 

    try: 
        await context.bot.send_photo(
            chat_id = moderador["id"],
            photo = GIF_LETRISTA,
            caption = "¡𝖤𝗇 𝗁𝗈𝗋𝖺 𝖻𝗎𝖾𝗇𝖺, 𝗍𝖾 𝗍𝗈𝖼𝖺 𝗌𝖾𝗋 𝖾𝗅 𝗆𝗈𝖽𝖾𝗋𝖺𝖽𝗈𝗋! 𝖯𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝖾𝗇𝗏𝗂𝖺 𝗅𝖺 𝗉𝖺𝗅𝖺𝖻𝗋𝖺 𝗊𝗎𝖾 𝖽𝖾𝗌𝗌𝖾𝗌 𝗌𝖾𝖺 𝖺𝖽𝗂𝗏𝗂𝗇𝖺𝖽𝖺"

        )

    except Exception:
        await context.bot.send_photo(
            chat_id = chat_id,
            photo = GIF_RECHAZADO,
            caption = f"𝖴𝗉𝗌, 𝗇𝗈 𝗌𝖾 𝗉𝗎𝖾𝖽𝖾 𝖾𝗇𝗏𝗂𝖺𝗋 𝗆𝖾𝗇𝗌𝖺𝗃𝖾 𝖺 ({moderador_id['name']}). 𝖯𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝖺𝗌𝖾𝗀𝗎𝗋𝖺𝗍𝖾 𝖽𝖾 𝗁𝖺𝖻𝖾𝗋 𝗂𝗇𝗂𝖼𝗂𝖺𝖽𝗈 𝖾𝗅 𝖻𝗈𝗍 𝖾𝗇 𝗉𝗋𝗂𝗏𝖺𝖽𝗈"
        )
        sesión[chat_id]["activa"] = False
        
# JUEGO 2: SNOWBALL 
async def unirse_snowball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sesión_bomba["jugadores"] = []
    sesión_bomba["activa"] = False
    boton = InlineKeyboardButton("੭੭ㅤㅤ𝐔𝐍𝐈𝐑𝐌𝐄ㅤㅤ!¡", callback_data="unirme_bomba_click")
    await update.message.reply_photo(
        photo = GIF_SNOWBALL,
        caption = "៹ ࣪  ❄️ ¡𝖩𝗎𝗀𝗎𝖾𝗆𝗈𝗌 𝖺𝗅 𝗌𝗇𝗈𝗐𝖻𝖺𝗅𝗅! 𝖯𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝗉𝗋𝖾𝗌𝗂𝗈𝗇𝖺 𝖾𝗅 𝖻𝗈𝗍𝗈𝗇 𝗉𝖺𝗋𝖺 𝗎𝗇𝗂𝗋𝗍𝖾 𝖺 𝗅𝖺 𝗉𝖺𝗋𝗍𝗂𝖽𝖺  ֪   𓂃", 
        reply_markup=InlineKeyboardMarkup([[boton]])
    )

async def iniciar_snowball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(sesión_bomba["jugadores"]) < 2:
        await update.message.reply_photo(
            photo = GIF_ERROR,
            caption = "𝖲𝖾 𝗇𝖾𝖼𝖾𝗌𝗂𝗍𝖺𝗇 𝗆𝗂𝗇𝗂𝗆𝗈 𝟤 𝗉𝖾𝗋𝗌𝗈𝗇𝖺𝗌 𝗉𝖺𝗋𝖺 𝗃𝗎𝗀𝖺𝗋. 𝖣𝖾 𝗍𝗋𝖺𝗍𝖺𝗋𝗌𝖾 𝗎𝗇 𝖾𝗋𝗋𝗈𝗋, 𝗉𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝗏𝗎𝖾𝗅𝗏𝖾 𝖺 𝗂𝗇𝗂𝖼𝗂𝖺𝗋 𝖾𝗅 𝗃𝗎𝖾𝗀𝗈."
        )
        return
    
    sesión_bomba["activa"] = True
    primer_jugador = random.choice(["jugadores"])
    sesión_bomba["bomba_en"] = primer_jugador["id"]
    sesión_bomba["bomba_emoji"] = primer_jugador["emoji"]
    
    await update.message.reply_text(f"❄️ ’ ¡𝖫𝖠 𝖡𝖮𝖫𝖠 𝖧𝖠 𝖲𝖨𝖣𝖮 𝖥𝖮𝖱𝖬𝖠𝖣𝖠!. 𝖧𝖺 𝖼𝖺𝗂𝖽𝗈 𝖾𝗇 𝗆𝖺𝗇𝗈𝗌 𝖽𝖾 {primer_jugador['name']} ✶")    
sesión_bomba["tarea_bomba"] = asyncio.create_task(cuenta_regresiva_bomba(chat_id, context))

async def cuenta_regresiva_bomba(chat_id, context):
    tiempo_explotar = random.randint(10, 25) 
    
    botones = []
    for jugador in sesión_bomba["jugadores"]:
        if jugador["id"] != sesión_bomba["bomba_en"]: 
            botones.append([InlineKeyboardButton(f"𝖫𝖺𝗇𝗓𝖺𝗋 𝖺 {jugador['emoji']}", callback_data=f"pasar_a_{jugador['id']}")])
    
    mensaje_bomba = await context.bot.send_message(
        chat_id=chat_id, 
        text=f"¡𝖣𝖺𝗍𝖾 𝗉𝗋𝗂𝗌𝖺 𝗒 𝖽𝖾𝗌𝗁𝖺𝖼𝖾𝗍𝖾 𝖽𝖾 𝖾𝗅𝗅𝖺!",
        reply_markup=InlineKeyboardMarkup(botones),
    )
    
    sesión_bomba["mensaje_id"] = mensaje_bomba.message_id
    await asyncio.sleep(tiempo_explotar)
    
    if sesión_bomba["activa"]:
        sesión_bomba["activa"] = False
        perdedor_id = sesión_bomba["bomba_en"]
        perdedor = next(j for j in sesión_bomba["jugadores"] if j['id'] == perdedor_id)
        
        texto_final = f"¡¡𝖮𝗁, 𝗇𝗈!! {perdedor['name']} 𝗇𝗈 𝗅𝗅𝖾𝗀𝗈 𝖺 𝗉𝖺𝗌𝖺𝗋 𝗅𝖺 𝖻𝗈𝗅𝖺 𝗒 𝗊𝗎𝖾𝖽𝗈 𝖺𝗉𝗅𝖺𝗌𝗍𝖺𝖽𝖺."
       
        
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=sesión_bomba["mensaje_id"], text=texto_final)
        except:
            await context.bot.send_message(chat_id=chat_id, text=texto_final)

# JUEGO 3: RATONES BATTLE ROYALE­
async def unirse_ratones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sesión_ratones["jugadores"] = []
    sesión_ratones["sobrevivientes"] = []
    sesión_ratones["activa"] = False
    boton = InlineKeyboardButton("੭੭ㅤㅤ𝐔𝐍𝐈𝐑𝐌𝐄ㅤㅤ!¡", callback_data="unirme_ratones_click")
    await update.message.reply_photo(
        photo = GIF_RATONES,
        caption = "៹ ࣪  🐭 ¡𝖩𝗎𝗀𝗎𝖾𝗆𝗈𝗌 𝖺 atrapar al ratón! 𝖯𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝗉𝗋𝖾𝗌𝗂𝗈𝗇𝖺 𝖾𝗅 𝖻𝗈𝗍𝗈𝗇 𝗉𝖺𝗋𝖺 𝗎𝗇𝗂𝗋𝗍𝖾 𝖺 𝗅𝖺 𝗉𝖺𝗋𝗍𝗂𝖽𝖺  ֪   𓂃",
        reply_markup=InlineKeyboardMarkup([[boton]])
    )

async def iniciar_ratones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if sesión_ratones.get("activa", False):
        await update.message.reply_text("¡𝖫𝗈 𝗌𝗂𝖾𝗇𝗍𝗈, 𝗒𝖺 𝗁𝖺𝗒 𝗎𝗇𝖺 𝗋𝗈𝗇𝖽𝖺 𝖾𝗇 𝖼𝗎𝗋𝗌𝗈!")
        return
    
    if len(sesión_ratones["jugadores"]) < 2:
        await update.message.reply_photo(
            photo = GIF_ERROR,
            caption = "𝖲𝖾 𝗇𝖾𝖼𝖾𝗌𝗂𝗍𝖺𝗇 𝗆𝗂𝗇𝗂𝗆𝗈 𝟤 𝗉𝖾𝗋𝗌𝗈𝗇𝖺𝗌 𝗉𝖺𝗋𝖺 𝗃𝗎𝗀𝖺𝗋. 𝖣𝖾 𝗍𝗋𝖺𝗍𝖺𝗋𝗌𝖾 𝗎𝗇 𝖾𝗋𝗋𝗈𝗋, 𝗉𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝗏𝗎𝖾𝗅𝗏𝖾 𝖺 𝗂𝗇𝗂𝖼𝗂𝖺𝗋 𝖾𝗅 𝗃𝗎𝖾𝗀𝗈."
        )
        return

    sesión_ratones["activa"] = True
    sesión_ratones["sobrevivientes"] = [j["id"] for j in sesión_ratones["jugadores"]]
    await update.message.reply_text("¡𝖫𝗈𝗌 𝗋𝖺𝗍𝗈𝗇𝖾𝗌 𝖾𝗌𝗍𝖺𝗇 𝗅𝗂𝗌𝗍𝗈𝗌 𝗉𝖺𝗋𝖺 𝗌𝖺𝗅𝗂𝗋!. ¡𝖠𝗍𝖾𝗇𝗍𝗈𝗌!...")
    asyncio.create_task(rondas_battle_royale(chat_id, context))

async def rondas_battle_royale(chat_id, context):
    ronda = 1
    while sesión_ratones["activa"] and len(sesión_ratones["sobrevivientes"]) > 1:
        await asyncio.sleep(random.randint(3, 5))
        vivos = [next(j['name'] for j in sesión_ratones["jugadores"] if j['id'] == uid) for uid in sesión_ratones["sobrevivientes"]]
        await context.bot.send_message(chat_id=chat_id, text=f"𝖧𝗈𝗋𝖽𝖺: {ronda}\n\n𝖨𝗆𝗉𝗅𝗂𝖼𝖺𝖽𝗈𝗌: {', '.join(vivos)}")
        await asyncio.sleep(2)


        await asyncio.sleep(2)

        # Matriz de botones 3x3
        botones = [[InlineKeyboardButton("🕳️", callback_data="raton_fallo") for _ in range(3)] for _ in range(3)]
        botones[random.randint(0, 2)][random.randint(0, 2)] =InlineKeyboardButton("🐭", callback_data="raton_salvado")
        
        sesión_ratones["esperando_click"] = list(sesión_ratones["sobrevivientes"])
        sesión_ratones["ronda_activa"] = True  
        
        sesión_ratones["mensaje_id"] = await context.bot.send_message(
            chat_id=chat_id, text="¡𝖴𝗇 𝗋𝖺𝗍𝗈𝗇 𝗌𝖾 𝖺𝖼𝖺𝖻𝖺 𝖽𝖾 𝖺𝗌𝗈𝗆𝖺𝗋, 𝖺𝗉𝗋𝖾𝗌𝗎𝗋𝖺𝗍𝖾 𝖺 𝖺𝗍𝗋𝖺𝗉𝖺𝗋𝗅𝗈!", reply_markup=InlineKeyboardMarkup(botones)

        # Esperar un maximo de 7 segundos a que clickeen, o que la ronda cierre por clicks
        limite = 7.0
        while limite > 0 and sesión_ratones["ronda_activa"]:
            await asyncio.sleep(0.5)
            limite -= 0.5

        # Borrar el panel de botones al terminar el tiempo o los clicks
        try: await context.bot.delete_message(chat_id=chat_id, message_id=sesión_ratones["mensaje_id"].message_id)
        except: pass

        # ⏱️ SI NADIE LE PICÓ O PASÓ EL TIEMPO SIN QUEDAR SÓLO UNO:

        if sesión_ratones["ronda_activa"] and len(sesión_ratones["esperando_click"]) > 0:
            # El último de la lista de espera queda fuera
            lento_id = sesión_ratones["esperando_click"][-1]
            lento_name = next(j['name'] for j in sesión_ratones["jugadores"] if j['id'] == lento_id)
            
            if lento_id in sesión_ratones["sobrevivientes"]:
                sesión_ratones["sobrevivientes"].remove(lento_id)
                
            await context.bot.send_message(
                chat_id=chat_id, 
                text=f"¡{lento_name} 𝖿𝗎𝖾 𝗆𝗎𝗒 𝗅𝖾𝗇𝗍𝗈 𝗒 𝖾𝗅 𝗋𝖺𝗍𝗈𝗇 𝗅𝗈𝗀𝗋𝗈 𝖾𝗌𝖼𝖺𝗉𝖺𝗋!. 𝖰𝗎𝖾𝖽𝖺 𝖿𝗎𝖾𝗋𝖺 𝖽𝖾𝗅 𝗃𝗎𝖾𝗀𝗈"
            )

        ronda += 1
        await asyncio.sleep(3)  # Pausa dramática entre rondas automática

    # Fin definitivo del juego
    sesión_ratones["activa"] = False
    if len(sesión_ratones["sobrevivientes"]) == 1:
        ganador_name = next(j['name'] for j in sesión_ratones["jugadores"] if j['id'] == sesión_ratones["sobrevivientes"][0])
        await context.bot.send_message(chat_id=chat_id, text=f"¡{ganador_name} 𝗁𝖺 𝗍𝖾𝗋𝗆𝗂𝗇𝖺𝖽𝗈 𝖼𝗈𝗇 𝗅𝖺 𝗉𝗅𝖺𝗀𝖺 𝖽𝖾 𝗋𝖺𝗍𝗈𝗇𝖾𝗌, 𝖿𝖾𝗅𝗂𝖼𝗂𝖽𝖺𝖽𝖾𝗌!")

# JUEGO 4: RITMO A GO-GO (STOP) 👏
async def unirse_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sesión_stop["jugadores"] = []
    sesión_stop["activa"] = False
    boton = InlineKeyboardButton("੭੭ㅤㅤ𝐔𝐍𝐈𝐑𝐌𝐄ㅤㅤ!¡", callback_data="unirme_stop_click")
    await update.message.reply_photo(
        photo = GIF_RITMOAGO,
        caption = "៹ ࣪  🎶 ¡𝖩𝗎𝗀𝗎𝖾𝗆𝗈𝗌 𝖺 𝗋𝗂𝗍𝗆𝗈 𝖺𝗀𝗈 𝗀𝗈! 𝖯𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝗉𝗋𝖾𝗌𝗂𝗈𝗇𝖺 𝖾𝗅 𝖻𝗈𝗍𝗈𝗇 𝗉𝖺𝗋𝖺 𝗎𝗇𝗂𝗋𝗍𝖾 𝖺 𝗅𝖺 𝗉𝖺𝗋𝗍𝗂𝖽𝖺  ֪   𓂃", 
        reply_markup=InlineKeyboardMarkup([[boton]])
    )

async def iniciar_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if len(sesión_stop["jugadores"]) < 2:
        await update.message.reply_photo(
            photo = GIF_ERROR,
            caption = "𝖲𝖾 𝗇𝖾𝖼𝖾𝗌𝗂𝗍𝖺𝗇 𝗆𝗂𝗇𝗂𝗆𝗈 𝟤 𝗉𝖾𝗋𝗌𝗈𝗇𝖺𝗌 𝗉𝖺𝗋𝖺 𝗃𝗎𝗀𝖺𝗋. 𝖣𝖾 𝗍𝗋𝖺𝗍𝖺𝗋𝗌𝖾 𝗎𝗇 𝖾𝗋𝗋𝗈𝗋, 𝗉𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝗏𝗎𝖾𝗅𝗏𝖾 𝖺 𝗂𝗇𝗂𝖼𝗂𝖺𝗋 𝖾𝗅 𝗃𝗎𝖾𝗀𝗈."
        )

        return
    
    sesión_stop["activa"] = True
    sesión_stop["sobrevivientes"] = [j["id"] for j in sesión_stop["jugadores"]]
    sesión_stop["palabras_dichas"] = []
    sesión_stop["turno_index"] = 0
    sesión_stop["letra_actual"] = random.choice("𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗝𝗟𝗠𝗡𝗢𝗣𝗥𝗦𝗧𝗨")
    sesión_stop["categoria_actual"] = random.choice(CATEGORIAS_STOP)
    
    await update.message.reply_text(
       f"¡𝖱𝖨𝖳𝖬𝖮 𝖠𝖦𝖮 𝖦𝖮, 𝖣𝖨𝖦𝖠 𝖴𝖲𝖳𝖤𝖣 𝖭𝖮𝖬𝖡𝖱𝖤𝖲 𝖣𝖤 {sesión_stop['categoria_actual']} 𝖢𝖮𝖭 𝖫𝖠 𝖫𝖤𝖳𝖱𝖠 {sesión_stop['letra_actual']} 𝖯𝖮𝖱 𝖤𝖩𝖤𝖬𝖯𝖫𝖮...\n\n¡𝖠𝗍𝖾𝗇𝗍𝗈𝗌 𝖺 𝗌𝗎 𝗍𝗎𝗋𝗇𝗈, 𝗌𝗈𝗅𝗈 𝗍𝖾𝗇𝖽𝗋𝖺𝗇 𝟣𝟧 𝗌𝖾𝗀𝗎𝗇𝖽𝗈𝗌 𝗉𝖺𝗋𝖺 𝗋𝖾𝗌𝗉𝗈𝗇𝖽𝖾𝗋!", 
    )

    await asyncio.sleep(5)
    await lanzar_turno_stop(chat_id, context)

async def lanzar_turno_stop(chat_id, context):
    if not sesión_stop["activa"]: return

    if len(sesión_stop["sobrevivientes"]) == 1:
        sesión_stop["activa"] = False
        ganador_name = next(j['name'] for j in sesión_stop["jugadores"] if j['id'] == sesión_stop["sobrevivientes"][0])
        await context.bot.send_message(chat_id=chat_id, text=ff"¡{ganador_name} 𝗀𝖺𝗇𝗈 𝗅𝖺 𝗋𝗈𝗇𝖽𝖺!")
        return

    actual_id = sesión_stop["sobrevivientes"][sesión_stop["turno_index"]]
    actual_name = next(j['name'] for j in sesión_stop["jugadores"] if j['id'] == actual_id)

    await context.bot.send_message(
        chat_id=chat_id, 
        text=f"¡{actual_name} 𝖾𝗌 𝗍𝗎 𝗍𝗎𝗋𝗇𝗈, 𝖺𝗉𝗋𝖾𝗌𝗎𝗋𝖺𝗍𝖾!"
    )

    if sesión_stop["timer_task"]: 
        sesión_stop["timer_task"].cancel()
    sesión_stop["timer_task"] = asyncio.create_task(timer_jugador_stop(chat_id, actual_id, actual_name, context))

async def timer_jugador_stop(chat_id, jugador_id, name, context):
    await asyncio.sleep(15)
    if sesión_stop["activa"] and sesión_stop["sobrevivientes"][sesión_stop["turno_index"]] == jugador_id:
        sesión_stop["sobrevivientes"].remove(jugador_id)
        await context.bot.send_message(chat_id=chat_id, text=f"¡{name} 𝗇𝗈 𝗋𝖾𝗌𝗉𝗈𝗇𝖽𝗂𝗈 𝖺 𝗍𝗂𝖾𝗆𝗉𝗈, 𝗆𝗎𝗒 𝗅𝖾𝗇𝗍𝗈, 𝗊𝗎𝖾𝖽𝖺 𝖾𝗅𝗂𝗆𝗂𝗇𝖺𝖽𝗈!")
        
        if sesión_stop["turno_index"] >= len(sesión_stop["sobrevivientes"]):
            sesión_stop["turno_index"] = 0
        
        await lanzar_turno_stop(chat_id, context)

# JUEGO 5: WHAT'S IN THE BOX 
async def unirse_box(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in sesión_jitb:
        sesión_jitb[chat_id] = {
            "jugadores": [],             # Lista de participantes de este grupo
            "activa": False,             # Estado del juego en este grupo
            "ultimo_encubridor_id": None # El Ãºltimo encubridor de este grupo
        }
    else:
        sesión_jitb[chat_id]["activa"] = False
        sesión_jitb[chat_id]["jugadores"] = []

    boton = InlineKeyboardButton("੭੭ㅤㅤ𝐔𝐍𝐈𝐑𝐌𝐄ㅤㅤ!¡", callback_data="unirme_box_click")
    await update.message.reply_photo(
        photo = GIF_JITB,
        caption = "៹ ࣪  📦 ¡𝖩𝗎𝗀𝗎𝖾𝗆𝗈𝗌 𝖺 𝗊𝗎𝖾 𝗁𝖺𝗒 𝖾𝗇 𝗅𝖺 𝖼𝖺𝗃𝖺! 𝖯𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝗉𝗋𝖾𝗌𝗂𝗈𝗇𝖺 𝖾𝗅 𝖻𝗈𝗍𝗈𝗇 𝗉𝖺𝗋𝖺 𝗎𝗇𝗂𝗋𝗍𝖾 𝖺 𝗅𝖺 𝗉𝖺𝗋𝗍𝗂𝖽𝖺  ֪   𓂃",
        reply_markup=InlineKeyboardMarkup([[boton]])
    )

async def iniciar_jitbx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in sesión_jitb or len(sesión_jitb[chat_id]["jugadores"]) < 2:
        await update.message.reply_photo(
            photo = GIF_ERROR,
            caption = "𝖲𝖾 𝗇𝖾𝖼𝖾𝗌𝗂𝗍𝖺𝗇 𝗆𝗂𝗇𝗂𝗆𝗈 𝟤 𝗉𝖾𝗋𝗌𝗈𝗇𝖺𝗌 𝗉𝖺𝗋𝖺 𝗃𝗎𝗀𝖺𝗋. 𝖣𝖾 𝗍𝗋𝖺𝗍𝖺𝗋𝗌𝖾 𝗎𝗇 𝖾𝗋𝗋𝗈𝗋, 𝗉𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝗏𝗎𝖾𝗅𝗏𝖾 𝖺 𝗂𝗇𝗂𝖼𝗂𝖺𝗋 𝖾𝗅 𝗃𝗎𝖾𝗀𝗈."
        )

        return     

    candidatos = list(sesión_jitb[chat_id]["jugadores"])
    ultimo_encubridor = sesión_jitb[chat_id].get("ultimo_encubridor_id")
    if ultimo_encubridor and len(candidatos) > 1:
        filtrados = [j for j in candidatos if j["id"] != ultimo_encubridor]
        if filtrados:
            encubridor = random.choice(filtrados)
        else:
            encubridor = random.choice(candidatos)
    else:
        encubridor = random.choice(candidatos)
    
    sesión_jitb[chat_id].update({
        "encubridor_id": encubridor["id"], 
        "ultimo_encubridor_id": encubridor["id"], 
        "activa": True
    })
    
    esperando_elementos[encubridor["id"]] = chat_id
    await update.message.reply_text(
        f"˒˓   ¡𝖤𝗇𝖼𝗎𝖻𝗋𝗂𝖽𝗈𝗋 𝖾𝗅𝖾𝗀𝗂𝖽𝗈!. 𝖤𝗌𝗉𝖾𝗋𝖺𝗇𝖽𝗈 𝗊𝗎𝖾 𝗌𝖾 𝖺𝗌𝗂𝗀𝗇𝖾𝗇 𝗅𝗈𝗌 𝗈𝖻𝗃𝖾𝗍𝗈𝗌 𝗉𝖺𝗋𝖺 𝗉𝗈𝖽𝖾𝗋 𝗂𝗇𝗂𝖼𝗂𝖺𝗋 𝖾𝗅 𝗃𝗎𝖾𝗀𝗈  ᨦᨩ")

    try:
        await context.bot.send_photo(
            chat_id = encubridor["id"],
            photo = GIF_ENCUBRIDOR, 
            caption = (
               "¡𝖤𝗇 𝗁𝗈𝗋𝖺 𝖻𝗎𝖾𝗇𝖺, 𝗍𝖾 𝗍𝗈𝖼𝖺 𝗌𝖾𝗋 𝖾𝗅 𝖾𝗇𝖼𝗎𝖻𝗋𝗂𝖽𝗈𝗋!\n\n"
                "𝖯𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝖾𝗇𝗏𝗂𝖺 𝖾𝗑𝖺𝖼𝗍𝖺𝗆𝖾𝗇𝗍𝖾 𝟨 𝖾𝗆𝗈𝗃𝗂𝗌 𝗌𝖾𝗉𝖺𝗋𝖺𝖽𝗈𝗌 𝗉𝗈𝗋 𝖾𝗌𝗉𝖺𝖼𝗂𝗈𝗌 (🌸 🌟 📰...), 𝗌𝖾𝗋𝖺𝗇 𝗆𝗈𝗌𝗍𝗋𝖺𝖽𝗈𝗌 𝖻𝗋𝖾𝗏𝖾𝗆𝖾𝗇𝗍𝖾 𝖺 𝗅𝗈𝗌 𝗉𝖺𝗋𝗍𝗂𝖼𝗂𝗉𝖺𝗇𝗍𝖾𝗌 𝖽𝖾 𝗅𝖺 𝗉𝖺𝗋𝗍𝗂𝖽𝖺"
            )

        )
    except Exception as e:
        await update.message.reply_photo(
            photo = GIF_RECHAZADO, 
            caption = (
            f"𝖴𝗉𝗌, 𝗇𝗈 𝗌𝖾 𝗉𝗎𝖾𝖽𝖾 𝖾𝗇𝗏𝗂𝖺𝗋 𝗆𝖾𝗇𝗌𝖺𝗃𝖾 𝖺 @{encubridor.get('username', 'usuario')}. "
            f"𝖯𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝖺𝗌𝖾𝗀𝗎𝗋𝖺𝗍𝖾 𝖽𝖾 𝗁𝖺𝖻𝖾𝗋 𝗂𝗇𝗂𝖼𝗂𝖺𝖽𝗈 𝖾𝗅 𝖻𝗈𝗍 𝖾𝗇 𝗉𝗋𝗂𝗏𝖺𝖽𝗈."))


# JUEGO 6: INFECCION ZOMBIE

async def unirse_zombie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    sesión_zombie["jugadores"] = []
    sesión_zombie["zombies"] = []
    sesión_zombie["vivos"] = []
    sesión_zombie["votos"] = {}
    sesión_zombie["activa"] = False
    sesión_zombie["fase"] = None
    
    boton = InlineKeyboardButton("੭੭  𝐔𝐍𝐈𝐑𝐌𝐄  !¡", callback_data="unirme_zombie_click")
    await update.message.reply_photo(
        photo = GIF_ZOMBIE, 
        caption = "៹ ࣪  🧟 𝖫𝖺 𝗇𝗈𝖼𝗁𝖾 𝗁𝖺 𝗅𝗅𝖾𝗀𝖺𝖽𝗈 𝗒 𝗅𝗈𝗌 𝗓𝗈𝗆𝖻𝗂𝖾𝗌 𝖾𝗌𝗍𝖺𝗇 𝖾𝗆𝗉𝖾𝗓𝖺𝖽𝗈 𝖺 𝗌𝖺𝗅𝗂𝗋 ¡𝖠𝗉𝗋𝖾𝗌𝗎𝗋𝖺𝗍𝖾 𝖺 𝗌𝗎𝖻𝗂𝗋𝗍𝖾 𝖺𝗅 𝖺𝗎𝗍𝗈𝖻𝗎𝗌!  ֪",
        reply_markup=InlineKeyboardMarkup([[boton]])
    )

async def iniciar_zombie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if sesión_zombie["activa"]:
        await update.message.reply_text("¡𝖫𝗈 𝗌𝗂𝖾𝗇𝗍𝗈, 𝗒𝖺 𝗁𝖺𝗒 𝗎𝗇𝖺 𝗋𝗈𝗇𝖽𝖺 𝖾𝗇 𝖼𝗎𝗋𝗌𝗈!")
        return
        
    if len(sesión_zombie["jugadores"]) < 3:
        await update.message.reply_animation(
            animation = GIF_ERROR,
            caption = "𝖲𝖾 𝗇𝖾𝖼𝖾𝗌𝗂𝗍𝖺𝗇 𝗆𝗂𝗇𝗂𝗆𝗈 𝟥 𝗉𝖾𝗋𝗌𝗈𝗇𝖺𝗌 𝗉𝖺𝗋𝖺 𝗃𝗎𝗀𝖺𝗋. 𝖣𝖾 𝗍𝗋𝖺𝗍𝖺𝗋𝗌𝖾 𝗎𝗇 𝖾𝗋𝗋𝗈𝗋, 𝗉𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝗏𝗎𝖾𝗅𝗏𝖾 𝖺 𝗂𝗇𝗂𝖼𝗂𝖺𝗋 𝖾𝗅 𝗃𝗎𝖾𝗀𝗈 "
        )

        return

    sesión_zombie["activa"] = True
    sesión_zombie["fase"] = "infeccion"
    sesión_zombie["vivos"] = [j["id"] for j in sesión_zombie["jugadores"]]
    
    paciente_cero_id = random.choice(sesión_zombie["vivos"])
    sesión_zombie["zombies"].append(paciente_cero_id)
    sesión_zombie["vivos"].remove(paciente_cero_id)
    
    paciente_cero_obj = next(j for j in sesión_zombie["jugadores"] if j["id"] == paciente_cero_id)
    
    await update.message.reply_text(
        "¡Un infectado se colo! Uno de ustedes fue mordido por un zombie 𝖺𝗇𝗍𝖾𝗌 𝖽𝖾 𝗌𝗎𝖻𝗂𝗋 𝖺𝗅 𝖺𝗎𝗍𝗈𝖻𝗎𝗌, el brote ha comenzado..."
    )
    
    botones_ataque = []
    for humano_id in sesión_zombie["vivos"]:
        humano_obj = next(j for j in sesión_zombie["jugadores"] if j["id"] == humano_id)
        botones_ataque.append([InlineKeyboardButton(f"𝖬𝗈𝗋𝖽𝖾𝗋 𝖺 {humano_obj['name']}", callback_data=f"morder:{humano_id}:{chat_id}")])
        
    try:
        await context.bot.send_photo(
            chat_id = paciente_cero_id,
            photo = GIF_CERO, 
            caption = "𝖥𝗎𝗂𝗌𝗍𝖾 𝗂𝗇𝖿𝖾𝖼𝗍𝖺𝖽𝗈 𝖺𝗇𝗍𝖾𝗌 𝖽𝖾 𝖾𝗇𝗍𝗋𝖺𝗋 𝖺𝗅 𝖺𝗎𝗍𝗈𝖻𝗎𝗌 𝗒 𝖺𝗁𝗈𝗋𝖺 𝗌𝗂𝖾𝗇𝗍𝖾𝗌 𝗎𝗇𝖺 𝗇𝖾𝖼𝖾𝗌𝗂𝖽𝖺𝖽 𝗂𝗇𝗍𝖾𝗇𝗌𝖺 𝖽𝖾 𝖼𝖺𝗋𝗇𝖾. ¿𝖰𝗎𝗂𝖾𝗇 𝗌𝖾𝗋𝖺 𝗍𝗎 𝗉𝗋𝖾𝗌𝖺?",
            reply_markup = InlineKeyboardMarkup(botones_ataque)
        )
    except Exception:
        await context.bot.send_message(
            chat_id = chat_id,
            text = f"𝖴𝗉𝗌, 𝗇𝗈 𝗌𝖾 𝗉𝗎𝖾𝖽𝖾 𝖾𝗇𝗏𝗂𝖺𝗋 𝗆𝖾𝗇𝗌𝖺𝗃𝖾 𝖺 ({paciente_cero_obj['name']}). 𝖯𝗈𝗋 𝖿𝖺𝗏𝗈𝗋, 𝖺𝗌𝖾𝗀𝗎𝗋𝖺𝗍𝖾 𝖽𝖾 𝗁𝖺𝖻𝖾𝗋 𝗂𝗇𝗂𝖼𝗂𝖺𝖽𝗈 𝖾𝗅 𝖻𝗈𝗍 𝖾𝗇 𝗉𝗋𝗂𝗏𝖺𝖽𝗈"
        )

        sesión_zombie["activa"] = False

async def abrir_votacion_zombie(chat_id, context):
    sesión_zombie["fase"] = "votacion"
    sesión_zombie["votos"] = {} 
    
    botones_voto = []
    for jugador in sesión_zombie["jugadores"]:
        botones_voto.append([InlineKeyboardButtonf"𝖤𝗑𝗉𝗎𝗅𝗌𝖺𝗋 𝖺 {jugador['name']}", callback_data=f"voto_z:{jugador['id']}"])
    
    msg_voto = await context.bot.send_message(
        chat_id = chat_id,
        text = (
            "¡𝖱𝖾𝗎𝗇𝗂𝗈𝗇 𝖽𝖾 𝖾𝗆𝖾𝗋𝗀𝖾𝗇𝖼𝗂𝖺! 𝖠𝗅𝗀𝗎𝗂𝖾𝗇 𝗒𝖺 𝖿𝗎𝖾 𝗆𝗈𝗋𝖽𝗂𝖽𝗈 𝖺𝗌𝗂 𝗊𝗎𝖾 𝖽𝖾𝖻𝖾𝗇 𝖾𝗑𝗉𝗎𝗅𝗌𝖺𝗋 𝖺𝗅 𝗂𝗇𝖿𝖾𝖼𝗍𝖺𝖽𝗈 𝖺𝗇𝗍𝖾𝗌 𝖽𝖾 𝗊𝗎𝖾 𝗆𝗎𝖾𝗋𝖽𝖺 𝖺 𝗈𝗍𝗋𝖺 𝗉𝖾𝗋𝗌𝗈𝗇𝖺, 𝗌𝗈𝗅𝗈 𝖼𝗎𝖾𝗇𝗍𝖺𝗇 𝖼𝗈𝗇 𝟣𝟤𝟢 𝗌𝖾𝗀𝗎𝗇𝖽𝗈𝗌 𝗉𝖺𝗋𝖺 𝗉𝗈𝗇𝖾𝗋𝗌𝖾 𝖽𝖾 𝖺𝖼𝗎𝖾𝗋𝖽𝗈 𝗒 𝗏𝗈𝗍𝖺𝗋"
        ),

        reply_markup = InlineKeyboardMarkup(botones_voto)
    )
    sesión_zombie["mensaje_voto_id"] = msg_voto.message_id
    
    asyncio.create_task(timer_votacion_zombie(chat_id, context))

async def timer_votacion_zombie(chat_id, context):
    await asyncio.sleep(120)
    if sesión_zombie["activa"] and sesión_zombie["fase"] == "votacion":
        await procesar_resultados_votacion(chat_id, context)

async def procesar_resultados_votacion(chat_id, context):
    sesión_zombie["fase"] = None
    
    try: await context.bot.delete_message(chat_id=chat_id, message_id=sesión_zombie["mensaje_voto_id"])
    except: pass
    
    if not sesión_zombie["votos"]:
        await context.bot.send_message(chat_id=chat_id, text="𝖭𝖺𝖽𝗂𝖾 𝗏𝗈𝗍𝗈 𝖺 𝗍𝗂𝖾𝗆𝗉𝗈, 𝖾𝗅 𝗂𝗇𝖿𝖾𝖼𝗍𝖺𝖽𝗈 𝗌𝗂𝗀𝗎𝖾 𝖺𝗊𝗎ı́, 𝖾𝗅 𝖺𝗍𝖺𝗊𝗎𝖾 𝖼𝗈𝗇𝗍𝗂𝗇𝗎𝖺...")
        await pasar_a_siguiente_ataque(chat_id, context)
        return

    conteo = {}
    for vid in sesión_zombie["votos"].values():
        conteo[vid] = conteo.get(vid, 0) + 1
        
    mas_votado_id = max(conteo, key=conteo.get)
    max_votos = conteo[mas_votado_id]
    
    empates = [k for k, v in conteo.items() if v == max_votos]
    if len(empates) > 1:
        await context.bot.send_message(chat_id=chat_id, text="¡𝖧𝗎𝖻𝗈 𝗎𝗇 𝖾𝗆𝗉𝖺𝗍𝖾 𝗒 𝗇𝖺𝖽𝗂𝖾 𝖿𝗎𝖾 𝖾𝗑𝗉𝗎𝗅𝗌𝖺𝖽𝗈!")
        await pasar_a_siguiente_ataque(chat_id, context)
        return
        
    eliminado_obj = next(j for j in sesión_zombie["jugadores"] if j["id"] == mas_votado_id)
    
    if mas_votado_id in sesión_zombie["zombies"]:
        sesión_zombie["zombies"].remove(mas_votado_id)
        sesión_zombie["jugadores"] = [j for j in sesión_zombie["jugadores"] if j["id"] != mas_votado_id]
        
        await context.bot.send_message(
            chat_id = chat_id,
            text = f"{eliminado_obj['name']} 𝗈𝖻𝗍𝗎𝗏𝗈 {max_votos} 𝗏𝗈𝗍𝗈𝗌 𝗒 𝖿𝗎𝖾 𝖾𝗑𝗉𝗎𝗅𝗌𝖺𝖽𝗈 𝖽𝖾𝗅 𝖺𝗎𝗍𝗈𝖻𝗎𝗌. ¡𝖥𝖾𝗅𝗂𝖼𝗂𝖽𝖺𝖽𝖾𝗌, 𝗌𝖾 𝖽𝖾𝗌𝗁𝗂𝖼𝗂𝖾𝗋𝗈𝗇 𝖽𝖾𝗅 𝗂𝗇𝖿𝖾𝖼𝗍𝖺𝖽𝗈!"
        )
    else:
        sesión_zombie["vivos"].remove(mas_votado_id)
        sesión_zombie["jugadores"] = [j for j in sesión_zombie["jugadores"] if j["id"] != mas_votado_id]
        
        await context.bot.send_message(
            chat_id = chat_id,
            text = f"{eliminado_obj['name']} 𝗈𝖻𝗍𝗎𝗏𝗈 {max_votos} 𝗏𝗈𝗍𝗈𝗌 𝗒 𝖿𝗎𝖾 𝖾𝗑𝗉𝗎𝗅𝗌𝖺𝖽𝗈 𝖽𝖾𝗅 𝖺𝗎𝗍𝗈𝖻𝗎𝗌. 𝖤𝗋𝖺 𝗎𝗇 𝗁𝗎𝗆𝖺𝗇𝗈 𝗉𝖾𝗋𝖿𝖾𝖼𝗍𝖺𝗆𝖾𝗇𝗍𝖾 𝗌𝖺𝗇𝗈..."
        )


    if not sesión_zombie["zombies"]:
        await context.bot.send_message(chat_id=chat_id, text="¡𝖲𝖮𝖡𝖱𝖤𝖵𝖨𝖵𝖨𝖤𝖱𝖮𝖭!. 𝖤𝗅 𝗂𝗇𝖿𝖾𝖼𝗍𝖺𝖽𝗈 𝖿𝗎𝖾 𝖾𝗑𝗉𝗎𝗅𝗌𝖺𝖽𝗈 𝖽𝖾𝗅 𝖺𝗎𝗍𝗈𝖻𝗎𝗌 𝗒 𝖺𝗁𝗈𝗋𝖺 𝗉𝗎𝖾𝖽𝖾𝗇 𝗏𝗈𝗅𝗏𝖾𝗋 𝖺 𝖼𝖺𝗌𝖺")
        sesión_zombie["activa"] = False
    elif not sesión_zombie["vivos"]:
        await context.bot.send_message(chat_id=chat_id, text="¡𝖸𝖺 𝗇𝗈 𝗊𝗎𝖾𝖽𝖺𝗇 𝗁𝗎𝗆𝖺𝗇𝗈𝗌! 𝖤𝗅 𝖺𝗎𝗍𝗈𝖻𝗎𝗌 𝗌𝖾 𝖼𝗈𝗇𝗏𝗂𝗋𝗍𝗂𝗈 𝖾𝗇 𝗈𝗍𝗋𝗈 𝖿𝗈𝖼𝗈 𝖽𝖾 𝗂𝗇𝖿𝖾𝖼𝖼𝗂𝗈𝗇")
        sesión_zombie["activa"] = False
    else:
        await pasar_a_siguiente_ataque(chat_id, context)

async def pasar_a_siguiente_ataque(chat_id, context):
    sesión_zombie["fase"] = "infeccion"
    
    for z_id in sesión_zombie["zombies"]:
        botones_ataque = []
        for humano_id in sesión_zombie["vivos"]:
            humano_obj = next(j for j in sesión_zombie["jugadores"] if j["id"] == humano_id)
            botones_ataque.append([InlineKeyboardButton(f"𝖬𝗈𝗋𝖽𝖾𝗋 𝖺 {humano_obj['name']}", callback_data=f"morder:{humano_id}:{chat_id}")])
            
        try:
            await context.bot.send_message(
                chat_id = z_id,
                text = "𝖮𝗍𝗋𝖺 𝗏𝖾𝗓 𝗌𝗂𝖾𝗇𝗍𝖾𝗌 𝖺𝗇𝗌𝗂𝖾𝖽𝖺𝖽 𝗉𝗈𝗋 𝗉𝗋𝗈𝖻𝖺𝗋 𝖼𝖺𝗋𝗇𝖾. 𝖤𝗅𝗂𝗀𝗎𝖾 𝖺 𝗍𝗎 𝗌𝗂𝗀𝗎𝗂𝖾𝗇𝗍𝖾 𝗏𝗂𝖼𝗍𝗂𝗆𝖺 𝖼𝗈𝗇 𝗉𝗋𝖾𝖼𝖺𝗎𝖼𝗂𝗈𝗇",
                reply_markup = InlineKeyboardMarkup(botones_ataque)
            )
        except: pass
    
    await context.bot.send_message(chat_id=chat_id, text="𝖫𝖺 𝗇𝗈𝖼𝗁𝖾 𝖼𝖺𝖾 𝗒 𝗌𝖾 𝖽𝖾𝖻𝖾𝗇 𝗉𝖺𝗀𝖺𝗋 𝗅𝖺𝗌 𝗅𝗎𝖼𝖾𝗌 𝖽𝖾𝗅 𝖺𝗎𝗍𝗈𝖻𝗎𝗌... 𝖤𝗅 𝗂𝗇𝖿𝖾𝖼𝗍𝖺𝖽𝗈 𝖾𝗌𝗍𝖺 𝖺𝗅 𝖺𝖼𝖾𝖼𝗁𝗈")
        
# 9. MANEJADOR DE CALLBACKS (BOTONES) 

async def manejar_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat_id = query.message.chat.id

    # Callbacks Ahorcado
    if query.data == "unirme_click":
        await query.answer()
        if chat_id not in sesión: 
            sesión[chat_id] = {"jugadores": [], "activa": False}
        # 🛡️ Escudo Ahorcado Active
        if sesión[chat_id]["activa"]:
            await query.answer("¡𝖫𝗈 𝗌𝗂𝖾𝗇𝗍𝗈, 𝗇𝗈 𝗍𝖾 𝗉𝗎𝖾𝖽𝖾𝗌 𝗎𝗇𝗂𝗋, 𝗒𝖺 𝗁𝖺𝗒 𝗎𝗇𝖺 𝗋𝗈𝗇𝖽𝖺 𝖾𝗇 𝖼𝗎𝗋𝗌𝗈!", show_alert=True)
            return
        if not any(j['id'] == user.id for j in sesión[chat_id]["jugadores"]):
            sesión[chat_id]["jugadores"].append({"id": user.id, "name": user.first_name})
            await query.message.reply_text(f"📝 ֹ  {user.first_name} se unió 𓂃")

    # Callbacks Box
    elif query.data == "unirme_box_click":
        await query.answer()
        if chat_id not in sesión_jitb:
            sesión_jitb[chat_id] = {"jugadores": [], "activa": False}
        if sesión_jitb[chat_id]["activa"]:
            await query.answer("¡𝖫𝗈 𝗌𝗂𝖾𝗇𝗍𝗈, 𝗇𝗈 𝗍𝖾 𝗉𝗎𝖾𝖽𝖾𝗌 𝗎𝗇𝗂𝗋, 𝗒𝖺 𝗁𝖺𝗒 𝗎𝗇𝖺 𝗋𝗈𝗇𝖽𝖺 𝖾𝗇 𝖼𝗎𝗋𝗌𝗈!", show_alert=True)
            return
        if not any(j['id'] == user.id for j in sesión_jitb[chat_id]["jugadores"]):
            sesión_jitb[chat_id]["jugadores"].append({"id": user.id, "name": user.first_name, "username": user.username})
            await query.message.reply_text(f"📦 ֹ  {user.first_name} se unió 𓂃")

    # Callbacks Bomba
    elif query.data == "unirme_bomba_click":
        await query.answer()
        if sesión_bomba["activa"]: 
            await query.answer("¡𝖫𝗈 𝗌𝗂𝖾𝗇𝗍𝗈, 𝗇𝗈 𝗍𝖾 𝗉𝗎𝖾𝖽𝖾𝗌 𝗎𝗇𝗂𝗋, 𝗒𝖺 𝗁𝖺𝗒 𝗎𝗇𝖺 𝗋𝗈𝗇𝖽𝖺 𝖾𝗇 𝖼𝗎𝗋𝗌𝗈!", show_alert=True)
            return
        if not any(j['id'] == user.id for j in sesión_bomba["jugadores"]):
            emojis_usados = [j["emoji"] for j in sesión_bomba["jugadores"]]
            emojis_disponibles = [e for e in EMOJIS_BOMBA if e not in emojis_usados]
            emoji_asignado = random.choice(emojis_disponibles) if emojis_disponibles else random.choice(EMOJIS_BOMBA)
            
            sesión_bomba["jugadores"].append({"id": user.id, "name": user.first_name, "emoji": emoji_asignado})
            await query.message.reply_text(f"❄️ ֹ  {user.first_name} se unió 𓂃")

    elif query.data.startswith("pasar_a_"):
        await query.answer()
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
                nuevos_botones.append([InlineKeyboardButton(f"𝖫𝖺𝗇𝗓𝖺𝗋 𝖺 {jugador['emoji']}", callback_data=f"pasar_a_{jugador['id']}")])
        
        await query.message.edit_text(
            text=f"¡{user_jugador['name']} 𝗌𝖾 𝗌𝖺𝗅𝗏𝗈 𝖽𝖾 𝗆𝗂𝗅𝖺𝗀𝗋𝗈!\n\n¡𝖠𝗁𝗈𝗋𝖺 𝗅𝖺 𝗍𝗂𝖾𝗇𝖾 {nuevo_jugador['name']}!\n¡𝖱𝖺́𝗉𝗂𝖽𝗈, 𝗉𝖺𝗌𝖺𝗌𝖾𝗅𝖺 𝖺 𝗈𝗍𝗋𝖺 𝗉𝖾𝗋𝗌𝗈𝗇𝖺!",
            reply_markup=InlineKeyboardMarkup(nuevos_botones)
        )

    # Callbacks Ratones
    elif query.data == "unirme_ratones_click":
        await query.answer()
        # 🛡️ Escudo Ratones Active
        if sesión_ratones["activa"]:
            await query.answer("¡𝖫𝗈 𝗌𝗂𝖾𝗇𝗍𝗈, 𝗇𝗈 𝗍𝖾 𝗉𝗎𝖾𝖽𝖾𝗌 𝗎𝗇𝗂𝗋, 𝗒𝖺 𝗁𝖺𝗒 𝗎𝗇𝖺 𝗋𝗈𝗇𝖽𝖺 𝖾𝗇 𝖼𝗎𝗋𝗌𝗈!", show_alert=True)
            return
        if not any(j['id'] == user.id for j in sesión_ratones["jugadores"]):
            sesión_ratones["jugadores"].append({"id": user.id, "name": user.first_name})
            await query.message.reply_text(f"🐭 ֹ  {user.first_name} se unió 𓂃")
            
    elif query.data == "raton_salvado":
        await query.answer()
        
        if sesión_ratones.get("activa") and sesión_ratones.get("ronda_activa") and user.id in sesión_ratones["esperando_click"]:
            sesión_ratones["esperando_click"].remove(user.id)
            await query.message.reply_text(f"¡{user.first_name} 𝗅𝗈𝗀𝗋𝗈 𝖺𝗉𝗅𝖺𝗌𝗍𝖺𝗋 𝖺𝗅 𝗋𝖺𝗍𝗈𝗇!")
            
            # 🚨 Si ya solo queda 1 jugador sin presionar, ¡tenemos al eliminado de la ronda!
            if len(sesión_ratones["esperando_click"]) == 1:
                sesión_ratones["ronda_activa"] = False # Rompe el timer del loop para avanzar de ronda
                
                eliminado_id = sesión_ratones["esperando_click"][0]
                eliminado_obj = next((j for j in sesión_ratones["jugadores"] if j["id"] == eliminado_id), None)
                eliminado_name = eliminado_obj["name"] if eliminado_obj else "Alguien"
                
                if eliminado_id in sesión_ratones["sobrevivientes"]:
                    sesión_ratones["sobrevivientes"].remove(eliminado_id)
                
                sesión_ratones["esperando_click"] = []
                
                # Tu frase exacta
                await query.message.reply_text(
                    f"¡𝖧𝖮𝖱𝖣𝖠 𝖳𝖤𝖱𝖬𝖨𝖭𝖠𝖣𝖠!\n\n"
                    f"{eliminado_name} 𝖿𝗎𝖾 𝖾𝗅 𝗎́𝗅𝗍𝗂𝗆𝗈 𝖾𝗇 𝖺𝗉𝗅𝖺𝗌𝗍𝖺𝗋 𝖺𝗅 𝗋𝖺𝗍𝗈́𝗇, 𝗍𝖾 𝖺𝗍𝗋𝗂𝖻𝗎𝗒𝖾𝗌 𝖾𝗅 𝗍𝗋𝖺𝖻𝖺𝗃𝗈 𝖽𝖾 𝗈𝗍𝗋𝗈, ¡𝖥𝖴𝖤𝖱𝖠!"
                )
            return

    elif query.data == "raton_fallo":
        await query.answer()
        if sesión_ratones.get("activa") and sesión_ratones.get("ronda_activa") and user.id in sesión_ratones["esperando_click"]:
            await query.message.reply_text(f"¡{user.first_name} 𝗅𝖾 𝖽𝗂𝗈 𝖺 𝗎𝗇 𝗁𝗎𝖾𝖼𝗈 𝗏𝖺𝖼ı́𝗈 𝗒 𝖾𝗅 𝗋𝖺𝗍𝗈𝗇 𝖾𝗌𝖼𝖺𝗉𝗈!")
            return
            
    # Callbacks STOP
    elif query.data == "unirme_stop_click":
        await query.answer()
        # 🛡️ Escudo Stop Active
        if sesión_stop["activa"]:
            await query.answer("¡𝖫𝗈 𝗌𝗂𝖾𝗇𝗍𝗈, 𝗇𝗈 𝗍𝖾 𝗉𝗎𝖾𝖽𝖾𝗌 𝗎𝗇𝗂𝗋, 𝗒𝖺 𝗁𝖺𝗒 𝗎𝗇𝖺 𝗋𝗈𝗇𝖽𝖺 𝖾𝗇 𝖼𝗎𝗋𝗌𝗈!", show_alert=True)
            return
        if not any(j['id'] == user.id for j in sesión_stop["jugadores"]):
            sesión_stop["jugadores"].append({"id": user.id, "name": user.first_name})
            await query.message.reply_text(f"📝 ֹ  {user.first_name} se unió 𓂃")

# === Callbacks Juego Zombie ===
    elif query.data == "unirme_zombie_click":
        if sesión_zombie.get("activa", False):
            await query.answer"¡𝖫𝗈 𝗌𝗂𝖾𝗇𝗍𝗈, 𝗇𝗈 𝗍𝖾 𝗉𝗎𝖾𝖽𝖾𝗌 𝗎𝗇𝗂𝗋, 𝗒𝖺 𝗁𝖺𝗒 𝗎𝗇𝖺 𝗋𝗈𝗇𝖽𝖺 𝖾𝗇 𝖼𝗎𝗋𝗌𝗈!", show_alert=True)
            return
        if not any(j['id'] == user.id for j in sesión_zombie["jugadores"]):
            sesión_zombie["jugadores"].append({"id": user.id, "name": user.first_name})
            await query.message.reply_text(f"🚌 ֹ  {user.first_name} se unió 𓂃")
        await query.answer()

    elif query.data.startswith("morder:"):
        await query.answer()
        partes = query.data.split(":")
        victima_id = int(partes[1])
        grupo_chat_id = int(partes[2])
        
        if sesión_zombie.get("activa", False) and sesión_zombie.get("fase") == "infeccion":
            if user.id in sesión_zombie.get("zombies", []):
                if victima_id in sesión_zombie["vivos"]:
                    sesión_zombie["vivos"].remove(victima_id)
                    sesión_zombie["zombies"].append(victima_id)
                
                    victima_obj = next(j for j in sesión_zombie["jugadores"] if j["id"] == victima_id)
                    await query.edit_message_text(f"𝖠𝗍𝖺𝗊𝗎𝖾 𝖾𝗑𝗂𝗍𝗈𝗌𝗈. 𝖧𝖺𝗌 𝗂𝗇𝖿𝖾𝖼𝗍𝖺𝖽𝗈 𝖺 {victima_obj['name']}.")
                
                    # 📢 ANUNCIO EN EL GRUPO: Avisamos quién murió/fue infectado
                    await context.bot.send_message(
                        chat_id = grupo_chat_id,
                        text = f"¡𝖴𝖭 𝖠𝖳𝖠𝖰𝖴𝖤 𝖧𝖠 𝖮𝖢𝖴𝖱𝖱𝖨𝖣𝖮!\n\n{victima_obj['name']} 𝗁𝖺 𝗌𝗂𝖽𝗈 𝖺𝗍𝖺𝖼𝖺𝖽𝗈 𝖾𝗇 𝗅𝖺 𝗈𝗌𝖼𝗎𝗋𝗂𝖽𝖺𝖽 𝗉𝗈𝗋 𝗎𝗇 𝗓𝗈𝗆𝖻𝗂𝖾 𝗒 𝗌𝖾 𝖾𝗌𝗍𝖺́ 𝗍𝗋𝖺𝗇𝗌𝖿𝗈𝗋𝗆𝖺𝗇𝖽𝗈, 𝗍𝗎𝗏𝗈 𝗊𝗎𝖾 𝗌𝖾𝗋 𝖾𝗑𝗉𝗎𝗅𝗌𝖺𝖽𝗈 𝖽𝖾 𝗂𝗇𝗆𝖾𝖽𝗂𝖺𝗍𝗈"
                    )

                
                    # Un pequeño delay de 2 segundos para el drama antes de la votación
                    await asyncio.sleep(2)
                
                    await abrir_votacion_zombie(grupo_chat_id, context)
                else:
                    await query.edit_message_text("𝖤𝗌𝗍𝖺 𝗏𝗂𝖼𝗍𝗂𝗆𝖺 𝗒𝖺 𝗇𝗈 𝖾𝗌𝗍𝖺 𝖽𝗂𝗌𝗉𝗈𝗇𝗂𝖻𝗅𝖾.")

    elif query.data.startswith("voto_z:"):
        await query.answer()
        votado_id = int(query.data.split(":")[1])
    
        if sesión_zombie.get("activa", False) and sesión_zombie.get("fase") == "votacion":
            if any(j['id'] == user.id for j in sesión_zombie["jugadores"]):
                sesión_zombie["votos"][user.id] = votado_id
                await query.answer(f"{user.first_name} 𝖺𝖼𝖺𝖻𝖺 𝖽𝖾 𝖾𝗆𝗂𝗍𝗂𝗋 𝗌𝗎 𝗏𝗈𝗍𝗈", show_alert=True)
            else:
                await query.answer("𝖴𝗉𝗌, 𝗍𝗎 𝗇𝗈 𝖾𝗌𝗍𝖺𝗌 𝗉𝖺𝗋𝗍𝗂𝖼𝗂𝗉𝖺𝗇𝖽𝗈 𝖾𝗇 𝖾𝗌𝗍𝖺 𝗉𝖺𝗋𝗍𝗂𝖽𝖺.", show_alert=True)

# =====================================================================
# 10. MANEJADOR DE MENSAJES (TEXTO)
# =====================================================================
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
        
        await update.message.reply_text("¡𝖯𝖺𝗅𝖺𝖻𝗋𝖺 𝗀𝗎𝖺𝗋𝖽𝖺𝖽𝖺! 𝖵𝗎𝖾𝗅𝗏𝖾 𝖺𝗅 𝗀𝗋𝗎𝗉𝗈.")
        guiones = " ".join(["_" if c != " " else "  " for c in texto])
        await context.bot.send_message(chat_id=gid, text=f"¡𝖤𝗅 𝗆𝗈𝖽𝖾𝗋𝖺𝖽𝗈𝗋 𝗁𝖺 𝗁𝖺𝖻𝗅𝖺𝖽𝗈!\n\n𝖯𝖠𝖫𝖠𝖡𝖱𝖠: '{guiones}’')
        return

    # Setup jack in the box por privado
    if chat_type == "private" and user_id in esperando_elementos:
        gid = esperando_elementos[user_id]

        emojis_originales = list(texto.replace(" ", ""))
        if len(emojis_originales) != 6:
            await update.message.reply_text("¡Alto ahi! Esos no son 6 elementos, por favor, vuelve a enviar")
            return      
        
        sesión_jitb[gid].update({
            "emojis_secretos": emojis_originales,      # Los 6 que deben adivinar
            "emojis_adivinados": [],                  # AquÃ­ meteremos los que ya descubrieron
            "puntajes": {},                           # GuardarÃ¡ {user_id: puntos}
            "activa": True
        })

        del esperando_elementos[user_id]
        await update.message.reply_text("¡𝖬𝗎𝖼𝗁𝖺𝗌 𝗀𝗋𝖺𝖼𝗂𝖺𝗌, 𝗅𝗈𝗌 𝟨 𝖾𝗅𝖾𝗆𝖾𝗇𝗍𝗈𝗌 𝗁𝖺𝗇 𝗌𝗂𝖽𝗈 𝗀𝗎𝖺𝗋𝖽𝖺𝖽𝗈𝗌!")
        
        lista_visual = " ".join(emojis_originales)
        mensaje_flash = await context.bot.send_message(
            chat_id=gid,
            text=f"¡𝖫𝖠 𝖢𝖠𝖩𝖠 𝖲𝖤𝖱𝖠 𝖠𝖡𝖨𝖤𝖱𝖳𝖠! \n\n 𝖬𝖾𝗆𝗈𝗋𝗂𝗓𝖺 𝖻𝗂𝖾𝗇 𝗅𝗈𝗌 𝖾𝗅𝖾𝗆𝖾𝗇𝗍𝗈𝗌, 𝖽𝖾𝗌𝖺𝗉𝖺𝗋𝖾𝖼𝖾𝗋𝖺𝗇 𝖾𝗇 5 𝗌𝖾𝗀𝗎𝗇𝖽𝗈𝗌:\n\n{lista_visual}"
        )
        
        await asyncio.sleep(5)

        try:
            await context.bot.delete_message(chat_id=gid, message_id=mensaje_flash.message_id)
        except Exception:
            pass

        await context.bot.send_message(
            chat_id=gid,
            text="¡𝖫𝖠 𝖢𝖠𝖩𝖠 𝖥𝖴𝖤 𝖢𝖤𝖱𝖱𝖠𝖣𝖠!\nEnvia tus respuestas de uno en uno.\n𝖲𝗂 𝗅𝖾 𝖼𝗈𝗂𝗇𝖼𝗂𝖽𝖾𝗌 𝖼𝗈𝗇 𝗎𝗇𝗈 𝗊𝗎𝖾 𝖾𝗌𝗍𝖺𝖻𝖺 𝖾𝗇 𝗅𝖺 𝖼𝖺𝗃𝖺, 𝗍𝖾 𝗅𝗅𝖾𝗏𝖺𝗌 𝟣 𝗉𝗎𝗇𝗍𝗈."
        )
        return
        
    # Escucha del juego Ahorcado en el Grupo 🎯
    if chat_id in sesión and sesión[chat_id].get("activa") and "palabra_secreta" in sesión[chat_id]:
        if len(texto) == 1 and texto.isalpha():
            if user_id == sesión[chat_id].get("moderador_id"):
                await update.message.reply_text("¡𝖮𝗒𝖾! 𝖳𝗎́ 𝖾𝗋𝖾𝗌 𝗅𝖺 𝗆𝗈𝖽𝖾𝗋𝖺𝖽𝗈𝗋𝖺, 𝗇𝗈 𝗉𝗎𝖾𝖽𝖾𝗌 𝗃𝗎𝗀𝖺𝗋 𝖾𝗌𝗍𝖺 𝗋𝗈𝗇𝖽𝖺.")
                return
                
            datos = sesión[chat_id]
            if user_id not in datos["jugadores_vidas"]: 
                datos["jugadores_vidas"][user_id] = 6
                
            if datos["jugadores_vidas"][user_id] <= 0: 
                await update.message.reply_text(f"𝖰𝗎𝖾 𝗉𝖾𝗇𝖺 {user_name}, 𝗒𝖺 𝗇𝗈 𝖼𝗎𝖾𝗇𝗍𝖺𝗌 𝖼𝗈𝗇 𝗂𝗇𝗍𝖾𝗇𝗍𝗈𝗌 𝖽𝗂𝗌𝗉𝗈𝗇𝗂𝖻𝗅𝖾𝗌 𝖾𝗇 𝖾𝗌𝗍𝖺 𝗋𝗈𝗇𝖽𝖺.")
                return

            letra_ingresada = texto.lower()

            if letra_ingresada in datos["palabra_secreta"]:
                if letra_ingresada not in datos["letras_adivinadas"]: 
                    datos["letras_adivinadas"].append(letra_ingresada)
            else:
                datos["jugadores_vidas"][user_id] -= 1

            tablero = dibujar_pantalla_ahorcado(chat_id)
            await update.message.reply_text(
                f"𝖯𝖠𝖫𝖠𝖡𝖱𝖠: '{tablero}'\n"
                f"{user_name} 𝖼𝗎𝖾𝗇𝗍𝖺𝗌 𝖼𝗈𝗇 {datos['jugadores_vidas'][user_id]} 𝗂𝗇𝗍𝖾𝗇𝗍𝗈𝗌"
            )
            
            if "_" not in tablero.replace(" ", ""):
                await update.message.reply_text(f"¡{user_name}𝗀𝖺𝗇𝗈 𝖾𝗌𝗍𝖺 𝗋𝗈𝗇𝖽𝖺!. Efectivamente, la palabra era: {datos['palabra_secreta'].upper()}")
                datos["activa"] = False
            return

    # Escucha del juego Jack In The Box en el Grupo 🕵️‍♂️
    if chat_type != "private" and chat_id in sesión_jitb and sesión_jitb[chat_id].get("activa"):
        sesion = sesión_jitb[chat_id]
        if texto in sesion.get("emojis_secretos", []) and texto not in sesion.get("emojis_adivinados", []):
            sesion["emojis_adivinados"].append(texto)
            sesion["puntajes"][user_id] = sesion["puntajes"].get(user_id, 0) + 1
            
            total_adivinados = len(sesion["emojis_adivinados"])
            await update.message.reply_text(
                f"¡𝖯𝗎𝗇𝗍𝗈 𝗉𝖺𝗋𝖺 {user_name}! 𝖤𝗅 𝗈𝖻𝗃𝖾𝗍𝗈 𝗌𝗂 𝖾𝗌𝗍𝖺𝖻𝖺 𝖽𝖾𝗇𝗍𝗋𝗈 𝖽𝖾 𝗅𝖺 𝖼𝖺𝗃𝖺\n"
                f"𝖫𝗅𝖾𝗏𝖺𝗆𝗈𝗌 [{total_adivinados} - 6] 𝗈𝖻𝗃𝖾𝗍𝗈𝗌 𝖽𝖾𝗌𝖼𝗎𝖻𝗂𝖾𝗋𝗍𝗈𝗌."
            )
            
            if total_adivinados == 6:
                sesion["activa"] = False
                
                # ─── RECUENTO DE PUNTAJES ───
                tabla_posiciones = []
                for uid, pts in sesion["puntajes"].items():
                    jugador_obj = next((j for j in sesion["jugadores"] if j["id"] == uid), None)
                    nombre_pantalla = jugador_obj["name"] if jugador_obj else f"Jugador ID: {uid}"
                    tabla_posiciones.append((nombre_pantalla, pts))
                
                tabla_posiciones.sort(key=lambda x: x[1], reverse=True)
                
                mensaje_recuento = "¡𝖱𝖮𝖭𝖣𝖠 𝖥𝖨𝖭𝖠𝖫𝖨𝖹𝖠𝖣𝖠! 𝖲𝖾 𝖽𝖾𝗌𝖼𝗎𝖻𝗋𝗂𝖾𝗋𝗈𝗇 𝗍𝗈𝖽𝗈𝗌 𝗅𝗈𝗌 𝗈𝖻𝗃𝖾𝗍𝗈𝗌 𝗊𝗎𝖾 𝗁𝖺𝖻𝗂𝖺𝗇 𝖽𝖾𝗇𝗍𝗋𝗈 𝖽𝖾 𝗅𝖺 𝖼𝖺𝗃𝖺. \n\n"
                mensaje_recuento += "𝖯𝗎𝗇𝗍𝗎𝖺𝖼𝗂𝗈𝗇 𝖿𝗂𝗇𝖺𝗅: \n"
                
                medallas = ["🥇", "🥈", "🥉""]
                for index, (nombre, puntos) in enumerate(tabla_posiciones):
                    decorador = medallas[index] if index < len(medallas) else "ðŸ”¹"
                    mensaje_recuento += f"{decorador} {nombre}: {puntos} pt(s)\n"
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=mensaje_recuento,
                )
            return

    # Escucha de Ritmo A Go-Go
    if sesión_stop.get("activa") and texto and not update.message.text.startswith("/"):
        if user_id in sesión_stop.get("sobrevivientes", []):
            actual_id = sesión_stop["sobrevivientes"][sesión_stop["turno_index"]]
            if user_id == actual_id:
                if sesión_stop.get("timer_task"): 
                    sesión_stop["timer_task"].cancel()

                palabra_limpia = texto.lower()
                eliminado = False

                if palabra_limpia in sesión_stop["palabras_dichas"]:
                    sesión_stop["sobrevivientes"].remove(user_id)
                    await update.message.reply_text(f"¡𝖠𝗅𝗍𝗈! '{texto}' 𝗒𝖺 𝗅𝖺 𝖽𝗂𝗃𝖾𝗋𝗈𝗇. 𝖰𝗎𝖾𝖽𝖺𝗌 𝖾𝗅𝗂𝗆𝗂𝗇𝖺𝖽𝗈 {user_name}")
                    eliminado = True
                elif not texto.upper().startswith(sesión_stop["letra_actual"].upper()):
                    sesión_stop["sobrevivientes"].remove(user_id)
                    await update.message.reply_text(f"𝖫𝖺 𝗉𝖺𝗅𝖺𝖻𝗋𝖺 𝗍𝖾𝗇𝗂𝖺 𝗊𝗎𝖾 𝖾𝗆𝗉𝖾𝗓𝖺𝗋 𝖼𝗈𝗇 {sesión_stop['letra_actual']}. 𝖰𝗎𝖾𝖽𝖺𝗌 𝖾𝗅𝗂𝗆𝗂𝗇𝖺𝖽𝗈 {user_name}")
                    eliminado = True
                else:
                    sesión_stop["palabras_dichas"].append(palabra_limpia)
                    await update.message.reply_text(f"¡𝖡𝗂𝖾𝗇 𝗁𝖾𝖼𝗁𝗈! '{texto}' 𝗁𝖺 𝗌𝗂𝖽𝗈 𝖺𝗇𝗈𝗍𝖺𝖽𝖺")

                # CORREGIDO: Verificación de Fin de Juego (Saber si queda un único ganador superviviente)
                if len(sesión_stop["sobrevivientes"]) <= 1:
                    sesión_stop["activa"] = False
                    if sesión_stop["sobrevivientes"]:
                        ganador_id = sesión_stop["sobrevivientes"][0]
                        ganador_obj = next((j for j in sesión_stop["jugadores"] if j["id"] == ganador_id), None)
                        g_name = ganador_obj["name"] if ganador_obj else "Alguien"
                        await context.bot.send_message(chat_id=chat_id, text=f"¡𝖩𝗎𝖾𝗀𝗈 𝗍𝖾𝗋𝗆𝗂𝗇𝖺𝖽𝗈!. 𝖤𝗌𝗍𝖺 𝗋𝗈𝗇𝖽𝖺 𝗅𝖺 𝗀𝖺𝗇𝗈 {g_name}")
                    else:
                        await context.bot.send_message(chat_id=chat_id, text=f"¡𝖩𝗎𝖾𝗀𝗈 𝗍𝖾𝗋𝗆𝗂𝗇𝖺𝖽𝗈!. 𝖭𝖺𝖽𝗂𝖾 𝗀𝖺𝗇𝗈 𝖾𝗇 𝖾𝗌𝗍𝖺 𝗈𝗉𝗈𝗋𝗍𝗎𝗇𝗂𝖽𝖺𝖽")
                    return

                # CORREGIDO: Ajuste seguro del índice de turnos tras eliminación
                if not eliminado:
                    sesión_stop["turno_index"] += 1

                if sesión_stop["turno_index"] >= len(sesión_stop["sobrevivientes"]):
                    sesión_stop["turno_index"] = 0

                await lanzar_turno_stop(chat_id, context)
                return


# =====================================================================
# 11. COMANDO DE CIERRE GENERAL
# =====================================================================
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

    # 5. 📦 APAGÓN TOTAL A JACK IN THE BOX
    if chat_id in sesión_jitb:
        sesión_jitb[chat_id]["activa"] = False
        sesión_jitb[chat_id]["jugadores"] = []

    # 7. 🧟 APAGÓN TOTAL A INFECCIÓN ZOMBIE
    sesión_zombie["activa"] = False
    sesión_zombie["jugadores"] = []
    sesión_zombie["zombies"] = []
    sesión_zombie["vivos"] = []
    sesión_zombie["fase"] = None

    await update.message.reply_photo(
        photo = GIF_OFFVAN,
        caption = "¡CLOSE VAN!\n\nSe cerraron todas las rondas existentes.")


# =====================================================================
# 12. BLOQUE PRINCIPAL DE ARRANQUE
# =====================================================================
if __name__ == '__main__':
    TOKEN = os.getenv("TOKEN_TELEGRAM")
    if TOKEN:
        keep_alive()
        application = ApplicationBuilder().token(TOKEN).build()
        
        # MENÃš PRINCIPAL Y CONFIG
        application.add_handler(CommandHandler("start", start_bienvenida))
        application.add_handler(CommandHandler("info", info))
        application.add_handler(CommandHandler("cmds", comandos))
        application.add_handler(CommandHandler("off_van", detener_juegos))

        # Handlers JUEGO 1: Ahorcado
        application.add_handler(CommandHandler("ahorcado", unirse_ahorcado))
        application.add_handler(CommandHandler("start_ahorcado", iniciar_ahorcado))
        
        # Handlers JUEGO 2: La Bomba
        application.add_handler(CommandHandler("snowball", unirse_snowball))
        application.add_handler(CommandHandler("start_snowball", iniciar_snowball))

        # Handlers JUEGO 3: Ratones
        application.add_handler(CommandHandler("ratones", unirse_ratones))
        application.add_handler(CommandHandler("start_ratones", iniciar_ratones))

        # Handlers JUEGO 4: Ritmo A Go-Go
        application.add_handler(CommandHandler("ritmo", unirse_stop))
        application.add_handler(CommandHandler("start_ritmo", iniciar_stop))

        # Handlers JUEGO 5: Jack In The Box
        application.add_handler(CommandHandler("box", unirse_box))
        application.add_handler(CommandHandler("start_box", iniciar_jitbx))

        # Handlers JUEGO 6: InfecciÃ³n Zombie
        application.add_handler(CommandHandler("zombie", unirse_zombie))
        application.add_handler(CommandHandler("start_zombie", iniciar_zombie))

        # Handlers de Botones y Mensajes Generales
        application.add_handler(CallbackQueryHandler(manejar_botones))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensajes))

        # ¡Arrancamos!
        application.run_polling()
