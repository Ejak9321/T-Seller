# Correctif pour "ModuleNotFoundError: No module named 'telegram'"
# La biblioth�que python-telegram-bot doit �tre install�e.
# Ajoutez "pip install python-telegram-bot" � l'environnement pour ex�cuter ce script.

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Dictionnaire pour stocker les utilisateurs approuv�s
approved_sellers = set()

# Dictionnaire pour stocker les produits publi�s {user_id: [products]}
products = {}

# ID du canal Telegram
CHANNEL_ID = "TON_ID_DU_CANAL"  # Remplacez par l'ID de votre canal

# ID de l'admin
ADMIN_ID = "TON_ID_ADMIN"  # Remplacez par votre propre ID d'admin

# Token du bot
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Remplacez par le token de votre bot

# Lien de l'image de v�rification
VERIFICATION_IMAGE_URL = "URL_IMAGE_VERIFICATION"  # Remplacez par le lien de l'image

# Commande de d�marrage
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [["Devenir Vendeur"], ["Demander une Collaboration"], ["Publier un Produit"], ["Modifier ou Retirer un Produit"]]
    await update.message.reply_text(
        "Bienvenue dans le bot?! Que souhaitez-vous faire??",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True),
    )

# Devenir vendeur
async def request_seller_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Pour devenir vendeur, veuillez publier l'affiche suivante sur :\n"
        f"1?? WhatsApp\n2?? TikTok\n3?? Facebook\n\n"
        f"Envoyez une capture d��cran pour chaque publication avec le lien du canal inclus.\n\n"
        f"Affiche : {VERIFICATION_IMAGE_URL}"
    )
    context.user_data["step"] = "seller_conditions"
    context.user_data["proofs"] = []

async def handle_seller_proofs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") == "seller_conditions":
        if update.message.photo:
            proof_id = update.message.photo[-1].file_id
            context.user_data["proofs"].append(proof_id)
            if len(context.user_data["proofs"]) < 3:
                await update.message.reply_text(
                    f"Capture re�ue ({len(context.user_data['proofs'])}/3). Envoyez la suivante."
                )
            else:
                await update.message.reply_text(
                    "Merci ! Appuyez sur le bouton ci-dessous pour soumettre votre demande.",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Demander une approbation", callback_data="request_approval")]]
                    ),
                )
        else:
            await update.message.reply_text("Veuillez envoyer une image valide.")

async def request_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    proofs = context.user_data.get("proofs", [])
    if proofs:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text="?? **Nouvelle demande d�approbation pour devenir vendeur**"
        )
        for proof in proofs:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=proof)
        await query.edit_message_text("Votre demande a �t� envoy�e. Un administrateur vous contactera bient�t.")
        context.user_data.clear()
    else:
        await query.edit_message_text("Aucune preuve d�tect�e. Veuillez recommencer.")

async def approve_seller(seller_id: str):
    approved_sellers.add(seller_id)

# Publier un produit
async def publish_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in approved_sellers:
        await update.message.reply_text(
            "Veuillez envoyer les informations du produit comme suit :\n"
            "1?? Nom du produit\n2?? Description\n3?? Cat�gorie\n4?? Prix\n5?? Photos (minimum 2)."
        )
        context.user_data["step"] = "publish_product"
    else:
        await update.message.reply_text(
            "Vous devez �tre un vendeur approuv� pour publier des produits. Veuillez d'abord demander une approbation."
        )

async def handle_product_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") == "publish_product":
        user_id = update.message.from_user.id
        product_info = update.message.text
        product_photos = update.message.photo

        if product_photos and len(product_photos) >= 2:
            if user_id not in products:
                products[user_id] = []
            products[user_id].append({"info": product_info, "photos": product_photos})

            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"?? Nouveau produit ajout� par {update.message.from_user.first_name} :\n{product_info}",
                photos=[photo.file_id for photo in product_photos]
            )

            await update.message.reply_text(
                "Produit publi� avec succ�s dans le canal !"
            )
        else:
            await update.message.reply_text(
                "Vous devez envoyer au moins deux photos pour publier un produit."
            )

# Modifier ou retirer un produit
async def manage_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in products and products[user_id]:
        product_list = "\n".join([f"{idx + 1}?? {p['info']}" for idx, p in enumerate(products[user_id])])
        await update.message.reply_text(
            f"Voici vos produits :\n{product_list}\n\n"
            "Envoyez le num�ro du produit pour le modifier ou le retirer."
        )
        context.user_data["step"] = "manage_product"
    else:
        await update.message.reply_text("Vous n'avez aucun produit enregistr�.")

async def handle_product_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if context.user_data.get("step") == "manage_product":
        try:
            choice = int(update.message.text) - 1
            if 0 <= choice < len(products[user_id]):
                selected_product = products[user_id][choice]
                await update.message.reply_text(
                    f"Produit s�lectionn� : {selected_product['info']}\n\n"
                    "Envoyez 'modifier' pour �diter ou 'retirer' pour supprimer."
                )
                context.user_data["selected_product"] = choice
            else:
                await update.message.reply_text("Num�ro invalide. Veuillez r�essayer.")
        except ValueError:
            await update.message.reply_text("Veuillez envoyer un num�ro valide.")

async def edit_or_remove_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    choice = context.user_data.get("selected_product")

    if choice is not None and choice < len(products[user_id]):
        action = update.message.text.lower()
        if action == "modifier":
            await update.message.reply_text(
                "Envoyez les nouvelles informations du produit comme suit :\n"
                "1?? Nom du produit\n2?? Description\n3?? Cat�gorie\n4?? Prix\n5?? Photos (minimum 2)."
            )
            context.user_data["step"] = "edit_product"
        elif action == "retirer":
            products[user_id].pop(choice)
            await update.message.reply_text("Produit supprim� avec succ�s.")
            context.user_data.pop("selected_product", None)
        else:
            await update.message.reply_text("Commande non reconnue. Envoyez 'modifier' ou 'retirer'.")
    else:
        await update.message.reply_text("Aucun produit valide s�lectionn�.")

async def update_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if context.user_data.get("step") == "edit_product":
        choice = context.user_data.get("selected_product")
        if choice is not None and choice < len(products[user_id]):
            products[user_id][choice]["info"] = update.message.text
            await update.message.reply_text("Produit modifi� avec succ�s.")
            context.user_data.pop("selected_product", None)

# Demander une collaboration
async def request_collaboration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Veuillez d�crire votre collaboration et inclure votre num�ro WhatsApp comme suit :\n"
        "Exemple : Je souhaite collaborer pour promouvoir vos produits. Mon num�ro est +228XXXXXXX."
    )
    context.user_data["step"] = "collaboration_request"

async def save_collaboration_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") == "collaboration_request":
        collaboration_info = update.message.text
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"??