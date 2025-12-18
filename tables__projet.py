from sqlmodel import Field, SQLModel, create_engine,Session,Relationship
from typing import List, Optional
import hashlib
import random
from datetime import date


def hash_mdp(mdp):
    m = mdp.encode()
    hsh = hashlib.sha256(m)
    return hsh.hexdigest()


class Administrateur(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str = Field(max_length=100)
    email: str
    mot_de_passe: str  
    role: str 

class Connexion_client(SQLModel,table=True):
    id:Optional[int] = Field(default=None, primary_key=True)
    client_id: Optional[int] = Field(default=None, foreign_key="client.client_id")
    email: str
    mot_de_passe: str
     

class Client(SQLModel, table=True):
    client_id: Optional[int] = Field(default=None, primary_key=True)
    nom: str 
    prenom: str 
    date_naissance: date
    email: str 
    telephone: str = Field(max_length=13)
    adresse: str = Field(max_length=255)
    profession: str = Field(max_length=100)
    solde_initial: float = Field(default=0.0)
    IBAN: str = Field(max_length=34)
    RIB: str = Field(max_length=50)
    numero_compte: str = Field(max_length=30)
    numero_carte: str = Field(max_length=20)
    date_expiration: str 
    cryptogramme: int
    transactions: List["Transaction"] = Relationship(back_populates="client")

class Transaction(SQLModel, table=True):
    id_transaction: Optional[int] = Field(default=None, primary_key=True)
    id_client: int = Field(foreign_key="client.client_id")
    nom_transaction: str = Field(max_length=100)
    date_transaction: date
    type_transaction: str = Field(max_length=30)
    categorie: str = Field(max_length=150)
    montant: float = Field(default=0.0)
    client: Optional["Client"] = Relationship(back_populates="transactions")

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args, echo=True)

def create_db_and_table():
    SQLModel.metadata.create_all(engine)

def reset_db():
    """Drop and recreate all tables (for development/seeding)."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def add_admin(nom: str, prenom:str, mot__de__passe: str, email: str,role:str):
    mdp=hash_mdp(mot__de__passe)
    print (mdp)
    with Session(engine) as session:
        new_admin = Administrateur(
            nom=nom.upper(),
            prenom=prenom,
            mot_de_passe=mdp,
            email=email,
            role=role
        )
        session.add(new_admin)
        session.commit()
        # session.refresh(new_admin)

def add_client(nom:str, prenom:str, date_naissance:date, email:str, telephone:str, adresse:str, 
               profession:str,solde_initial:int,IBAN:str, RIB:str, numero_compte:str, numero_carte:str, date_expiration:str, cryptogramme:int):
    with Session(engine) as session: 
        new_client=Client(
        nom=nom,
        prenom=prenom,
        date_naissance=date_naissance,
        email=email, 
        telephone=telephone,
        solde_initial=solde_initial,
        adresse=adresse,
        profession=profession,
        IBAN=IBAN,
        RIB=RIB,
        numero_compte=numero_compte,
        numero_carte=numero_carte,
        date_expiration=date_expiration,
        cryptogramme=cryptogramme
        )
        session.add(new_client)
        session.commit()
        # session.refresh(new_client)

def add_transaction( id_client:int, nom_transaction:str, date_transaction:date, type_transaction:str, categorie:str,montant:int):
     with Session(engine) as session: 
        new_trans=Transaction(
            id_client=id_client,
            nom_transaction=nom_transaction,
            date_transaction =date_transaction,
            type_transaction =type_transaction,
            categorie =categorie,
            montant=montant
        )
        session.add(new_trans)
        session.commit()
    
def main():
    # For development: reset the schema to match the current models
    reset_db()
  


    # Insertion des données
    with Session(engine) as session:
        # Administrateurs
        admin1 = Administrateur(
            id=1,
            nom="AdminPrincipal",
            mot_de_passe=hash_mdp("0123"),
            email="admin1@bankapp.com",
            role="admin"
        )
        admin2 = Administrateur(
            id=2,
            nom="Gestionnaire",
            mot_de_passe=hash_mdp("0000"),
            email="admin2@bankapp.com",
            role="admin"
        )

        # Clients
        client1 = Client(
            client_id=1,
            nom="Ngono",
            prenom="Paul",
            date_naissance=date(1990, 4, 12),
            email="paul.ngono@example.com",
            telephone="694123456",
            adresse="Yaoundé, Bastos",
            profession="Ingénieur logiciel",
            solde_initial=500000,
            IBAN="CM79 0020 3000 1234 5678 9012 345",
            RIB="30001 00001 12345678901 45",
            numero_compte="ACC00123456",
            numero_carte="4567 8923 5566 8910",
            date_expiration="07/28",
            cryptogramme="921"
        )

        client2 = Client(
            client_id=2,
            nom="Mbia",
            prenom="Clarisse",
            date_naissance=date(1985, 2, 25),
            email="clarisse.mbia@example.com",
            telephone="677987654",
            adresse="Douala, Bonapriso",
            profession="Comptable",
            solde_initial=400000,
            IBAN="CM79 0040 2000 9876 5432 1098 765",
            RIB="20004 00002 98765432109 76",
            numero_compte="ACC00987654",
            numero_carte="5234 7789 0012 3478",
            date_expiration="11/27",
            cryptogramme="553"
        )

        client3 = Client(
            client_id=3,
            nom="Fouda",
            prenom="Didier",
            date_naissance=date(1993, 10, 8),
            email="didier.fouda@example.com",
            telephone="650112233",
            adresse="Yaoundé, Essos",
            profession="Entrepreneur",
            solde_initial=1500000,
            IBAN="CM79 0050 1000 1122 3344 5566 778",
            RIB="10005 00003 11223344556 89",
            numero_compte="ACC00441122",
            numero_carte="4123 9987 3344 1122",
            date_expiration="03/29",
            cryptogramme="771"
            )

        con_clent1=Connexion_client(
            client_id=1,
            nom="Ngono".upper(),
            email="paul.ngono@example.com",
            mot_de_passe=hash_mdp("1980")
        )
        con_clent2=Connexion_client(
            client_id=2,
            nom="Mbia".upper(),
            email="clarisse.mbia@example.com",
            mot_de_passe=hash_mdp("1111")
        ) 
        con_clent3=Connexion_client(
            client_id=3,
            nom="Fouda".upper(),
            email="didier.fouda@example.com",
            mot_de_passe=hash_mdp("1234")
        )


        # Ajout et commit
        session.add(admin1)
        session.add(admin2)
        session.add(client1)
        session.add(client2)
        session.add(client3)
        session.add(con_clent1)
        session.add(con_clent2)
        session.add(con_clent3)
        session.commit()
        transactions_data =[
            # Client 1
            (1, "TR1-001-2025", date(2025, 1, 5), "dépôt", "Dépôt guichet",-15000),
            (1, "TR2-001-2025", date(2025, 1, 8), "paiement", "Paiement supermarché DOVV",-10000),
            (1, "TR3-001-2025", date(2025, 1, 12), "retrait", "Retrait ATM BICEC",-175000),
            (1, "TR4-001-2025", date(2025, 1, 18), "virement", "Virement vers compte épargne",-85000),
            (1, "TR5-001-2025", date(2025, 1, 22), "prélèvement", "Abonnement Canal+",-15000),
            (1, "TR6-001-2025", date(2025, 1, 29), "paiement", "Station-service Tradex",33000),
            (1, "TR7-002-2025", date(2025, 2, 3), "dépôt", "Dépôt mobile money",-5000),
            (1, "TR8-002-2025", date(2025, 2, 6), "paiement", "Location voiture",-12000),
            (1, "TR9-002-2025", date(2025, 2, 10), "retrait", "Retrait ATM Afriland",6115000),
            (1, "TR10-002-2025", date(2025, 2, 14), "prélèvement", "Netflix",-5000),
            (1, "TR11-002-2025", date(2025, 2, 21), "virement", "Virement vers époux",25000),

            # Client 2
            (2, "TR1-002-2025", date(2025, 1, 5), "dépôt", "Dépôt guichet",15000),
            (2, "TR2-002-2025", date(2025, 1, 8), "paiement", "Paiement supermarché DOVV",-10000),
            (2, "TR3-002-2025", date(2025, 1, 12), "retrait", "Retrait ATM BICEC",-175000),
            (2, "TR4-002-2025", date(2025, 1, 18), "virement", "Virement vers compte épargne",-85000),
            (2, "TR5-002-2025", date(2025, 1, 22), "prélèvement", "Abonnement Canal+",-15000),
            (2, "TR6-002-2025", date(2025, 1, 29), "paiement", "Station-service Tradex",33000),
            (2, "TR7-002-2025", date(2025, 2, 3), "dépôt", "Dépôt mobile money",5000),
            (2, "TR8-002-2025", date(2025, 2, 6), "paiement", "Pharmacie La Grâce",12000),
            (2, "TR9-002-2025", date(2025, 2, 10), "retrait", "Retrait ATM Afriland",75000),
            (2, "TR1-002-2025", date(2025, 2, 14), "prélèvement", "Netflix",5000),
            (2, "TR11-002-2025", date(2025, 2, 21), "virement", "Virement vers époux",40000),

            # Client 3
            (3, "TR11-003-2025", date(2025, 1, 8), "paiement", "Paiement supermarché DOVV",10000),
            (3, "TR10-003-2025", date(2025, 1, 12), "retrait", "Retrait ATM BICEC",175000),
            (3, "TR9-003-2025", date(2025, 1, 18), "virement", "Virement vers compte épargne",85000),
            (3, "TR8-003-2025", date(2025, 1, 22), "prélèvement", "Abonnement Canal+",15000),
            (3, "TR7-003-2025", date(2025, 1, 29), "paiement", "Station-service Tradex",33000),
            (3, "TR1-003-2025", date(2025, 3, 2), "paiement", "Restaurant Le Président",35000),
            (3, "TR2-003-2025", date(2025, 3, 4), "virement", "Paiement fournisseur",-540000),
            (3, "TR3-003-2025", date(2025, 3, 7), "dépôt", "Dépôt espèce",150000),
            (3, "TR4-003-2025", date(2025, 3, 11), "virement", "virement ATM UBA",500000),
            (3, "TR5-003-2025", date(2025, 3, 15), "paiement", "Supermarché Carrefour",-39000),
            (3, "TR6-003-2025", date(2025, 3, 22), "prélèvement", "Paiement assurance",-50000)
        ]


        

        random.shuffle(transactions_data)
        for id_client, nom_transaction, date_transaction, type_transaction, categorie,montant in transactions_data:
            add_transaction(id_client, nom_transaction, date_transaction, type_transaction, categorie,montant)


if __name__ == "__main__":
    main()
   
    



