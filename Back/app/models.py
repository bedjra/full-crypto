from app import db
from flask_sqlalchemy import SQLAlchemy

# Table Users
class User(db.Model):
    __tablename__ = 'users'  
    id = db.Column(db.Integer, primary_key=True)  
    email = db.Column(db.String(120), unique=True, nullable=False) 
    password = db.Column(db.String(200), nullable=False)  

    def __repr__(self):
        return f"<User {self.email}>"
    
# Table Transaction
class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    montant_FCFA = db.Column(db.Integer, nullable=False)  # Entier naturel
    taux_convenu = db.Column(db.Integer, nullable=False)  # Entier naturel
    montant_USDT = db.Column(db.Numeric(10, 2), nullable=False)  # Deux chiffres après la virgule
    date_transaction = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relation avec Fournisseur (1:N)
    fournisseurs = db.relationship('Fournisseur', backref='transaction', lazy=True, cascade="all, delete")

    def __repr__(self):
        return f"<Transaction {self.id}: {self.montant_FCFA} FCFA>"

# Table Fournisseur
class Fournisseur(db.Model):
    __tablename__ = 'fournisseurs'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    taux_jour = db.Column(db.Integer, nullable=False)  # Entier naturel
    quantite_USDT = db.Column(db.Numeric(10, 2), nullable=False)  # Deux chiffres après la virgule
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)

    # Relation avec Beneficiaire (1:N)
    beneficiaires = db.relationship('Beneficiaire', backref='fournisseur', lazy=True, cascade="all, delete")

    def __repr__(self):
        return f"<Fournisseur {self.nom}: {self.taux_jour} taux>"

# Table Beneficiaire
class Beneficiaire(db.Model):
    __tablename__ = 'beneficiaires'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    commission_USDT = db.Column(db.Numeric(10, 2), nullable=False)  # Deux chiffres après la virgule
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.id'), nullable=False)

    def __repr__(self):
        return f"<Beneficiaire {self.nom}: {self.commission_USDT} USDT>"





