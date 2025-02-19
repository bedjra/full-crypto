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

        # Vérification des champs requis pour le fournisseur
        if not all(k in data for k in ["nom", "taux_jour", "quantite_USDT", "transaction_id"]):
            return jsonify({"message": "Données incomplètes"}), 400

        # Création du fournisseur
        new_fournisseur = Fournisseur(
            nom=data["nom"],
            taux_jour=data["taux_jour"],
            quantite_USDT=data["quantite_USDT"],
            transaction_id=data["transaction_id"]
        )

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
        db.session.rollback()  # Annule la transaction en cas d'erreur
        return jsonify({"message": "Erreur lors de l'ajout", "error": str(e)}), 500

###############################################
#######  Get all FOURNISS ##################
@main.route('/all/four', methods=['GET'])
def get_all_fournisseurs():
    try:
        # Récupération de tous les fournisseurs
        fournisseurs = Fournisseur.query.all()

        # Construction de la réponse
        result = []
        for fournisseur in fournisseurs:
            # Récupération des bénéficiaires associés à chaque fournisseur
            beneficiaires = Beneficiaire.query.filter_by(fournisseur_id=fournisseur.id).all()

            result.append({
                "id": fournisseur.id,
                "nom": fournisseur.nom,
                "taux_jour": float(fournisseur.taux_jour),
                "quantite_USDT": float(fournisseur.quantite_USDT),
                "transaction_id": fournisseur.transaction_id,
                "beneficiaires": [
                    {
                        "id": benef.id,
                        "nom": benef.nom,
                        "commission_USDT": float(benef.commission_USDT)
                    } for benef in beneficiaires
                ]
            })

        return jsonify({
            "message": "Liste des fournisseurs récupérée avec succès",
            "fournisseurs": result
        }), 200

    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des fournisseurs", "error": str(e)}), 500





###############################################
#######  Get all fourn NOM ##################
@main.route('/all/four/nom', methods=['GET'])
def get_all_fournisseurs_noms():
    try:
        # Récupération des fournisseurs avec uniquement id et nom
        fournisseurs = Fournisseur.query.with_entities(Fournisseur.id, Fournisseur.nom).all()

        # Construction de la réponse
        result = [{"id": fournisseur.id, "nom": fournisseur.nom} for fournisseur in fournisseurs]

        return jsonify({
            "message": "Liste des noms des fournisseurs récupérée avec succès",
            "fournisseurs": result
        }), 200

    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des noms des fournisseurs", "error": str(e)}), 500


############################################
#######  get by id ####################
@main.route('/four/<int:id>', methods=['GET'])
def get_fournisseur_by_id(id):
    try:
        # Récupération du fournisseur par ID
        fournisseur = Fournisseur.query.get(id)

        if not fournisseur:
            return jsonify({"message": f"Fournisseur avec l'ID {id} introuvable"}), 404

        # Récupération de la transaction associée au fournisseur
        transaction = fournisseur.transaction

        # Récupération des bénéficiaires associés au fournisseur
        beneficiaires = Beneficiaire.query.filter_by(fournisseur_id=fournisseur.id).all()

        # Construction de la réponse
        result = {
            "id": fournisseur.id,
            "nom": fournisseur.nom,
            "taux_jour": float(fournisseur.taux_jour),
            "quantite_USDT": float(fournisseur.quantite_USDT),
            "transaction_id": fournisseur.transaction_id,
            "transaction": {
                "id": transaction.id,
                "montant_FCFA": transaction.montant_FCFA,
                "taux_convenu": transaction.taux_convenu,
                "montant_USDT": float(transaction.montant_USDT),
            } if transaction else None,
            "beneficiaires": [
                {
                    "id": benef.id,
                    "nom": benef.nom,
                    "commission_USDT": float(benef.commission_USDT)
                } for benef in beneficiaires
            ]
        }

        return jsonify({
            "message": "Fournisseur récupéré avec succès",
            "fournisseur": result
        }), 200

    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération du fournisseur", "error": str(e)}), 500

    try:
        # Récupération du fournisseur par ID
        fournisseur = Fournisseur.query.get(id)

        if not fournisseur:
            return jsonify({"message": f"Fournisseur avec l'ID {id} introuvable"}), 404

        # Récupération des bénéficiaires associés au fournisseur
        beneficiaires = Beneficiaire.query.filter_by(fournisseur_id=fournisseur.id).all()

        # Construction de la réponse
        result = {
            "id": fournisseur.id,
            "nom": fournisseur.nom,
            "taux_jour": float(fournisseur.taux_jour),
            "quantite_USDT": float(fournisseur.quantite_USDT),
            "transaction_id": fournisseur.transaction_id,
           
            "beneficiaires": [
                {
                    "id": benef.id,
                    "nom": benef.nom,
                    "commission_USDT": float(benef.commission_USDT)
                } for benef in beneficiaires
            ]
        }

        return jsonify({
            "message": "Fournisseur récupéré avec succès",
            "fournisseur": result
        }), 200

    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération du fournisseur", "error": str(e)}), 500


###############################################
#######  put four ##################
@main.route('/update/four/<int:id>', methods=['PUT'])
def update_fournisseur(id):
    try:
        data = request.get_json()

        # Récupération du fournisseur par ID
        fournisseur = Fournisseur.query.get(id)
        if not fournisseur:
            return jsonify({"message": "Fournisseur non trouvé"}), 404

        # Mise à jour des champs du fournisseur
        if "nom" in data:
            fournisseur.nom = data["nom"]
        if "taux_jour" in data:
            fournisseur.taux_jour = data["taux_jour"]
        if "quantite_USDT" in data:
            fournisseur.quantite_USDT = data["quantite_USDT"]
        if "transaction_id" in data:
            fournisseur.transaction_id = data["transaction_id"]

        # Gestion des bénéficiaires
        if "beneficiaires" in data:
            beneficiaires_data = data["beneficiaires"]
            if not isinstance(beneficiaires_data, list):
                return jsonify({"message": "La liste des bénéficiaires doit être un tableau"}), 400

            # Suppression des bénéficiaires existants
            Beneficiaire.query.filter_by(fournisseur_id=id).delete()

            # Ajout des nouveaux bénéficiaires
            for benef_data in beneficiaires_data:
                if "nom" not in benef_data or "commission_USDT" not in benef_data:
                    return jsonify({"message": "Chaque bénéficiaire doit avoir un 'nom' et une 'commission_USDT'"}), 400

                new_beneficiaire = Beneficiaire(
                    nom=benef_data["nom"],
                    commission_USDT=benef_data["commission_USDT"],
                    fournisseur_id=id
                )
                db.session.add(new_beneficiaire)

        db.session.commit()  # Commit des modifications

        # Récupération des bénéficiaires mis à jour
        beneficiaires_mis_a_jour = Beneficiaire.query.filter_by(fournisseur_id=id).all()

        return jsonify({
            "message": "Fournisseur et bénéficiaires mis à jour avec succès",
            "fournisseur": {
                "id": fournisseur.id,
                "nom": fournisseur.nom,
                "taux_jour": float(fournisseur.taux_jour),
                "quantite_USDT": float(fournisseur.quantite_USDT),
                "transaction_id": fournisseur.transaction_id,
                "beneficiaires": [
                    {"id": b.id, "nom": b.nom, "commission_USDT": float(b.commission_USDT)}
                    for b in beneficiaires_mis_a_jour
                ]
            }
        }), 200

    except Exception as e:
        db.session.rollback()  # Annule la transaction en cas d'erreur
        return jsonify({"message": "Erreur lors de la mise à jour", "error": str(e)}), 500

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

    # Vérification des données obligatoires
    if not data or not data.get('nom') or not data.get('commission_USDT') or not data.get('fournisseur_nom'):
        return jsonify({"message": "Données invalides"}), 400

    # Chercher le fournisseur par son nom (unique)
    fournisseur_nom = data['fournisseur_nom']
    fournisseur = Fournisseur.query.filter_by(nom=fournisseur_nom).first()

    if not fournisseur:
        return jsonify({"message": "Fournisseur introuvable"}), 404

    # Création du bénéficiaire sans lier immédiatement le fournisseur
    new_beneficiaire = Beneficiaire(
        nom=data['nom'],
        commission_USDT=data['commission_USDT'],
        fournisseur_id=fournisseur.id  # Associer directement le fournisseur lors de la création
    )

    db.session.add(new_beneficiaire)
    db.session.commit()

    # Retourner les informations du bénéficiaire ajouté avec le nom du fournisseur
    result = {
        "id": new_beneficiaire.id,
        "nom": new_beneficiaire.nom,
        "commission_USDT": new_beneficiaire.commission_USDT,
        "fournisseur_nom": fournisseur.nom  # Utiliser le nom du fournisseur
    }

    return jsonify({
        "message": "Bénéficiaire ajouté avec succès",
        "beneficiaire": result
    }), 200



###############################################
#######  Get all BENEF ##################
@main.route('/all/benef', methods=['GET'])
def get_all_beneficiaires():
    # Récupérer tous les bénéficiaires
    beneficiaires = Beneficiaire.query.all()

    # Si aucun bénéficiaire n'est trouvé
    if not beneficiaires:
        return jsonify({"message": "Aucun bénéficiaire trouvé"}), 404

    # Préparer la réponse avec les informations des bénéficiaires
    result = []
    for beneficiaire in beneficiaires:
        fournisseur = Fournisseur.query.get(beneficiaire.fournisseur_id)
        result.append({
            "id": beneficiaire.id,
            "nom": beneficiaire.nom,
            "commission_USDT": beneficiaire.commission_USDT,
            "fournisseur_nom": fournisseur.nom if fournisseur else "Inconnu"
        })

    return jsonify({
        "message": "Liste des bénéficiaires récupérée avec succès",
        "beneficiaires": result
    }), 200





###############################################
#######  Get  BENEF by ID  ##################
@main.route('/benef/<int:id>', methods=['GET'])
def get_beneficiaire_by_id(id):
    # Récupérer le bénéficiaire par son ID
    beneficiaire = Beneficiaire.query.get(id)
    
    # Vérifier si le bénéficiaire existe
    if not beneficiaire:
        return jsonify({"message": "Bénéficiaire non trouvé"}), 404
    
    # Récupérer le fournisseur associé
    fournisseur = Fournisseur.query.get(beneficiaire.fournisseur_id)
    
    # Préparer la réponse avec les détails du fournisseur
    result = {
        "id": beneficiaire.id,
        "nom": beneficiaire.nom,
        "commission_USDT": beneficiaire.commission_USDT,
        "fournisseur": {
            "id": fournisseur.id if fournisseur else None,
            "nom": fournisseur.nom if fournisseur else "Inconnu",
            "taux_jour": fournisseur.taux_jour if fournisseur else None,
            "quantite_USDT": float(fournisseur.quantite_USDT) if fournisseur else None
        }
    }
    
    return jsonify({
        "message": "Bénéficiaire récupéré avec succès",
        "beneficiaire": result
    }), 200




##############################################
#######  Modifier BENEF ##################
@main.route('/update/benef/<int:id>', methods=['PUT'])
def update_beneficiaire_by_id(id):
    data = request.get_json()

    # Vérification des données obligatoires
    if not data or not data.get('nom') or not data.get('commission_USDT') or not data.get('fournisseur_nom'):
        return jsonify({"message": "Données invalides"}), 400

    # Chercher le fournisseur par son nom (unique)
    fournisseur_nom = data['fournisseur_nom']
    fournisseur = Fournisseur.query.filter_by(nom=fournisseur_nom).first()

    if not fournisseur:
        return jsonify({"message": "Fournisseur introuvable"}), 404

    # Chercher le bénéficiaire par son ID
    beneficiaire = Beneficiaire.query.get(id)

    if not beneficiaire:
        return jsonify({"message": "Bénéficiaire introuvable"}), 404

    # Mise à jour des informations du bénéficiaire
    beneficiaire.nom = data['nom']
    beneficiaire.commission_USDT = data['commission_USDT']
    beneficiaire.fournisseur_id = fournisseur.id  # Associe le fournisseur au bénéficiaire

    # Enregistrer les modifications dans la base de données
    db.session.commit()

    # Retourner les informations du bénéficiaire mis à jour avec le fournisseur
    result = {
        "id": beneficiaire.id,
        "nom": beneficiaire.nom,
        "commission_USDT": beneficiaire.commission_USDT,
        "fournisseur_nom": fournisseur.nom  # Utilise le nom du fournisseur
    }

    return jsonify({
        "message": "Bénéficiaire mis à jour avec succès",
        "beneficiaire": result
    }), 200


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






    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################
############## DASHBORD ################## DASHBORD ##################
############## DASHBORD ################## DASHBORD ##################

#####################################################
#######  Get all four NUMBER TOTAL ##################
@main.route('/total/fr', methods=['GET'])
def get_total_fournisseurs():
    total_fournisseurs = Fournisseur.query.count()
    return jsonify({"total_fournisseurs": total_fournisseurs}), 200


#######################################################
#######  Get all transa NUMBER TOTAL ##################
@main.route('/total/tr', methods=['GET'])
def get_total_transactions():
    total_transactions = Transaction.query.count()  # Compter le nombre total de transactions
    return jsonify({"total": total_transactions}), 200

    
#######################################################
#######  Get all transa NUMBER TOTAL ##################
@main.route('/total/bn', methods=['GET'])
def get_total_beneficiaires():
    total_beneficiaires = Beneficiaire.query.count()
    return jsonify({"total_beneficiaires": total_beneficiaires}), 200








    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################
############## CALCUL ################## CALCUL ##################
############## CALCUL ################## CALCUL ##################
@main.route('/calculer', methods=['POST'])
def calculer():
    data = request.json
    montantFCFA = data.get('montantFCFA', 0)
    tauxConvenu = data.get('tauxConvenu', 0)
    tauxFournisseur = data.get('tauxFournisseur', 0)
    quantiteUSDT = data.get('quantiteUSDT', 0)
    commission = data.get('commission', 0)

    if tauxConvenu == 0:
        return jsonify({"error": "Le taux convenu ne peut pas être zéro"}), 400

    montantUSDT = montantFCFA / tauxConvenu
    beneficeParUSDT = tauxConvenu - tauxFournisseur
    beneficeTotalFCFA = beneficeParUSDT * quantiteUSDT
    beneficeBeneficiaire = commission * quantiteUSDT

    resultats = {
        "montantUSDT": round(montantUSDT, 2),
        "beneficeUSDT": round(beneficeParUSDT, 2),
        "beneficeTotalFCFA": round(beneficeTotalFCFA, 2),
        "beneficeBeneficiaire": round(beneficeBeneficiaire, 2),
        "totalBenefice": round(beneficeTotalFCFA, 2),
        "beneficeParBeneficiaire": round(beneficeBeneficiaire, 2)
    }
    
    return jsonify(resultats)

############## CALCUL GET ALL  ##########
@main.route('/cal', methods=['GET'])
def getalltransactions():
    transactions = Transaction.query.all()
    results = [
        {
            "id": t.id,
            "montantFCFA": t.montant_FCFA,
            "tauxConvenu": t.taux_convenu,
            "tauxFournisseur": t.taux_jour,
            "quantiteUSDT": t.quantiteUSDT,
            "commission": t.commission
        }
        for t in transactions
    ]
    return jsonify(results)

############## CALCUL LES 3 DERNIERS ############    
#@main.route('/transactions/last3', methods=['GET'])
#def get_last_three_transactions():
#    transactions = Transaction.query.order_by(Transaction.id.desc()).limit(3).all()
    # results = [
        # {
            # "id": t.id,
            # "montantFCFA": t.montantFCFA,
    #         "tauxConvenu": t.tauxConvenu,
    #         "tauxFournisseur": t.tauxFournisseur,
    #         "quantiteUSDT": t.quantiteUSDT,
    #         "commission": t.commission
    #     }
    #     for t in transactions
    # ]
    # return jsonify(results)


##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################    
##########################################################################################
##########################################################################################
############## HISTORIQUE ################## HISTORIQUE ##################
############## HISTORIQUE ################## HISTORIQUE ##################
