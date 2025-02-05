from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.models import Transaction , Fournisseur , Beneficiaire
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from datetime import datetime

main = Blueprint('main', __name__) 

##########################################################################################
##########################################################################################
@main.route('/save', methods=['POST'])
def save_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email et mot de passe sont requis !"}), 400

    # Vérifier si l'utilisateur existe déjà
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "Cet email est déjà utilisé !"}), 409

    # Hachage du mot de passe
    hashed_password = generate_password_hash(password)

    # Création et sauvegarde du nouvel utilisateur
    new_user = User(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Utilisateur enregistré avec succès !"}), 201
####### utilisateur login ##################
@main.route('/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Trouver l'utilisateur par email
    user = User.query.filter_by(email=email).first()

    # Si l'utilisateur n'existe pas ou le mot de passe est incorrect
    if user and check_password_hash(user.password, password):
        return jsonify({"message": "Connexion réussie !"}), 200
    else:
        return jsonify({"message": "Email ou mot de passe incorrect !"}), 401


###############################################
#######  Get all utilisateur ##################
@main.route('/user', methods=['GET'])
def get_user():
    email = request.args.get('email')  # Récupère l'email passé en paramètre de requête
    
    # Trouver l'utilisateur par email
    user = User.query.filter_by(email=email).first()

    if user:
        # Si l'utilisateur existe, renvoyer ses informations
        return jsonify({
            "id": user.id,
            "email": user.email,
        }), 200
    else:
        # Si l'utilisateur n'existe pas
        return jsonify({"message": "Utilisateur non trouvé !"}), 404 

##########################################################################################
##########################################################################################
####### formulaire AJOUT TRANSACTION ##################
@main.route('/trans/add', methods=['POST'])
def ajouter_transaction():
    try:
        data = request.json
        print("📩 Données reçues:", data)

        montant_fcfa = float(data.get('montantFCFA', 0))
        taux_conv = float(data.get('tauxConv', 0))

        if montant_fcfa <= 0 or taux_conv <= 0:
            return jsonify({'message': 'Données invalides'}), 400

        montant_usdt = montant_fcfa / taux_conv

        transaction = Transaction(
            montant_FCFA=montant_fcfa,
            taux_convenu=taux_conv,
            montant_USDT=montant_usdt
            # Pas besoin de 'dateTransaction', c'est géré par SQLAlchemy
        )

        db.session.add(transaction)
        db.session.commit()

        return jsonify({
            'message': 'Transaction ajoutée',
            'transaction': {
                'montantFCFA': montant_fcfa,
                'tauxConv': taux_conv,
                'montantUSDT': montant_usdt,
                'dateTransaction': transaction.date_transaction.isoformat()

            }
        }), 201

    except Exception as e:
        print("🔥 Erreur serveur:", str(e))
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500

##############################################
#######  DELETE TRANSACTION ##################
@main.route('/trans/delete/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    # Trouver la transaction par son ID
    transaction = Transaction.query.get(id)
    
    # Si la transaction n'existe pas
    if not transaction:
        return jsonify({"message": "Transaction non trouvée !"}), 404
    
    # Supprimer la transaction
    db.session.delete(transaction)
    db.session.commit()
    
    # Retourner un message de succès
    return jsonify({"message": "Transaction supprimée avec succès !"}), 200



##############################################
#######  Modifier TRANSACTION ################
@main.route('/trans/update/<int:id>', methods=['PUT'])
def update_transaction(id):
    # Trouver la transaction par son ID
    transaction = Transaction.query.get(id)

    # Si la transaction n'existe pas
    if not transaction:
        return jsonify({"message": "Transaction non trouvée !"}), 404
    
    # Récupérer les données envoyées en JSON
    data = request.json
    try:
        montant_fcfa = float(data.get('montantFCFA'))
        taux_conv = float(data.get('tauxConv'))
    except (TypeError, ValueError):
        return jsonify({'message': 'Données invalides, veuillez entrer des nombres'}), 400

    # Validation des données
    if montant_fcfa is None or taux_conv is None or taux_conv <= 0:
        return jsonify({'message': 'Données invalides'}), 400

    # Mettre à jour les champs de la transaction
    transaction.montant_FCFA = montant_fcfa
    transaction.taux_convenu = taux_conv
    transaction.montant_USDT = montant_fcfa / taux_conv  # Recalculer le montant en USDT
    transaction.date_transaction = db.func.current_timestamp()  # Mettre à jour la date de modification

    # Sauvegarder les modifications dans la base de données
    db.session.commit()

    # Retourner un message de succès avec les informations mises à jour
    return jsonify({
        "message": "Transaction mise à jour avec succès !",
        "transaction": {
            "id": transaction.id,
            "montantFCFA": transaction.montant_FCFA,
            "tauxConv": transaction.taux_convenu,
            "montantUSDT": transaction.montant_USDT,
            "dateTransaction": transaction.date_transaction
        }
    }), 200

###############################################
#######  Get all TRANSACTION ##################
@main.route('/trans/all', methods=['GET'])
def get_all_transactions():
    # Récupérer toutes les transactions
    transactions = Transaction.query.all()

    # Si aucune transaction n'est trouvée
    if not transactions:
        return jsonify({"message": "Aucune transaction trouvée."}), 404
    
    # Formater les résultats pour les renvoyer
    transactions_list = []
    for transaction in transactions:
        transactions_list.append({
            "id": transaction.id,
            "montantFCFA": str(transaction.montant_FCFA),  # Convertir en string pour JSON
            "tauxConv": str(transaction.taux_convenu),
            "montantUSDT": str(transaction.montant_USDT),
            "dateTransaction": transaction.date_transaction.isoformat()  # Format ISO pour DateTime
        })
    
    # Retourner les transactions sous forme de JSON
    return jsonify({"transactions": transactions_list}), 200




##########################################################################################
##########################################################################################
####### formulaire AJOUT Fournisseurs ##################
@main.route('/add/four', methods=['POST'])
def add_fournisseur():
    try:
        data = request.get_json()

        # Vérification des champs requis
        if not all(k in data for k in ["nom", "taux_jour", "quantite_USDT", "transaction_id"]):
            return jsonify({"message": "Données incomplètes"}), 400

        # Création du fournisseur
        new_fournisseur = Fournisseur(
            nom=data["nom"],
            taux_jour=data["taux_jour"],
            quantite_USDT=data["quantite_USDT"],
            transaction_id=data["transaction_id"]
        )

        # Enregistrement dans la base
        db.session.add(new_fournisseur)
        db.session.commit()

        return jsonify({
            "message": "Fournisseur ajouté avec succès",
            "fournisseur": {
                "id": new_fournisseur.id,
                "nom": new_fournisseur.nom,
                "taux_jour": float(new_fournisseur.taux_jour),
                "quantite_USDT": float(new_fournisseur.quantite_USDT),
                "transaction_id": new_fournisseur.transaction_id
            }
        }), 201

    except Exception as e:
        return jsonify({"message": "Erreur lors de l'ajout", "error": str(e)}), 500



###############################################
#######  Get all FOURNISS ##################
@main.route('/all/four', methods=['GET'])
def get_fournisseurs():
    try:
        # Récupérer tous les fournisseurs
        fournisseurs = Fournisseur.query.all()

        # Vérifier si des fournisseurs existent
        if not fournisseurs:
            return jsonify({"message": "Aucun fournisseur trouvé"}), 404

        # Transformation des données en JSON
        fournisseurs_list = []
        for fournisseur in fournisseurs:
            fournisseurs_list.append({
                "id": fournisseur.id,
                "nom": fournisseur.nom,
                "taux_jour": float(fournisseur.taux_jour),
                "quantite_USDT": float(fournisseur.quantite_USDT),
                "transaction_id": fournisseur.transaction_id
            })

        return jsonify({
            "message": "Fournisseurs récupérés avec succès",
            "fournisseurs": fournisseurs_list
        }), 200

    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des fournisseurs", "error": str(e)}), 500

##############################################
#######  Modifier Four ##################
@main.route('/update/four/<int:id>', methods=['PUT'])
def update_fournisseur(id):
    fournisseur = Fournisseur.query.get(id)
    if not fournisseur:
        return jsonify({"message": "Fournisseur introuvable"}), 404

    data = request.get_json()
    if "nom" in data:
        fournisseur.nom = data["nom"]
    if "taux_jour" in data:
        fournisseur.taux_jour = data["taux_jour"]
    if "quantite_USDT" in data:
        fournisseur.quantite_USDT = data["quantite_USDT"]
    if "transaction_id" in data:
        fournisseur.transaction_id = data["transaction_id"]

    db.session.commit()
    return jsonify({"message": "Fournisseur mis à jour avec succès"}), 200


##############################################
#######  DELETE FOUR ##################
@main.route('/delete/four/<int:id>', methods=['DELETE'])
def delete_fournisseur(id):
    fournisseur = Fournisseur.query.get(id)
    if not fournisseur:
        return jsonify({"message": "Fournisseur introuvable"}), 404

    db.session.delete(fournisseur)
    db.session.commit()
    return jsonify({"message": "Fournisseur supprimé avec succès"}), 200




##########################################################################################
##########################################################################################
####### formulaire AJOUT Benef ##################
@main.route('/add/benef', methods=['POST'])
def add_beneficiaire():
    data = request.get_json()
    if not data or not data.get('nom') or not data.get('commission_USDT') or not data.get('fournisseur_id'):
        return jsonify({"message": "Données invalides"}), 400

    fournisseur = Fournisseur.query.get(data['fournisseur_id'])
    if not fournisseur:
        return jsonify({"message": "Fournisseur introuvable"}), 404

    new_beneficiaire = Beneficiaire(
        nom=data['nom'],
        commission_USDT=data['commission_USDT'],
        fournisseur_id=data['fournisseur_id']
    )
    db.session.add(new_beneficiaire)
    db.session.commit()

    return jsonify({"message": "Bénéficiaire ajouté avec succès"}), 20


###############################################
#######  Get all BENEF ##################
@main.route('/all/benef', methods=['GET'])
def get_all_beneficiaires():
    beneficiaires = Beneficiaire.query.all()
    return jsonify([{
        "id": b.id,
        "nom": b.nom,
        "commission_USDT": float(b.commission_USDT),
        "fournisseur_id": b.fournisseur_id
    } for b in beneficiaires])

##############################################
#######  Modifier BENEF ##################
@main.route('/update/benef/<int:id>', methods=['PUT'])
def update_beneficiaire(id):
    beneficiaire = Beneficiaire.query.get(id)
    if not beneficiaire:
        return jsonify({"message": "Bénéficiaire introuvable"}), 404

    data = request.get_json()
    if "nom" in data:
        beneficiaire.nom = data["nom"]
    if "commission_USDT" in data:
        beneficiaire.commission_USDT = data["commission_USDT"]
    if "fournisseur_id" in data:
        fournisseur = Fournisseur.query.get(data['fournisseur_id'])
        if not fournisseur:
            return jsonify({"message": "Fournisseur introuvable"}), 404
        beneficiaire.fournisseur_id = data["fournisseur_id"]

    db.session.commit()
    return jsonify({"message": "Bénéficiaire mis à jour avec succès"}), 200

##############################################
#######  DELETE BENEF ##################
@main.route('/delete/benef/<int:id>', methods=['DELETE'])
def delete_beneficiaire(id):
    beneficiaire = Beneficiaire.query.get(id)
    if not beneficiaire:
        return jsonify({"message": "Bénéficiaire introuvable"}), 404

    db.session.delete(beneficiaire)
    db.session.commit()
    return jsonify({"message": "Bénéficiaire supprimé avec succès"}), 200