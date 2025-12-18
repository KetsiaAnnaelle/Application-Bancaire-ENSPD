from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Tuple
import hashlib

from flask import Flask, jsonify, request, send_from_directory, session
from sqlalchemy import case, func
from sqlmodel import Session, select

from tables__projet import (
    Transaction, Client, Administrateur, Connexion_client,
    create_db_and_table, engine, hash_mdp
)


def _parse_date(arg_name: str) -> Tuple[Optional[date], Optional[str]]:
    """
    Try to parse a YYYY-MM-DD query parameter into a date.
    Returns (value, error_message).
    """
    raw = request.args.get(arg_name)
    if not raw:
        return None, None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date(), None
    except ValueError:
        return None, f"Invalid {arg_name} format. Use YYYY-MM-DD."


def _apply_common_filters(stmt, start: Optional[date], end: Optional[date], client_id: Optional[int]):
    if start:
        stmt = stmt.where(Transaction.date_transaction >= start)
    if end:
        stmt = stmt.where(Transaction.date_transaction <= end)
    if client_id:
        stmt = stmt.where(Transaction.id_client == client_id)
    return stmt


def create_app() -> Flask:
    # Ensure tables exist before serving.
    create_db_and_table()

    app = Flask(__name__)
    app.secret_key = "finaily-gc-secret-key-2025"  # Change in production

    @app.get("/api/transactions/monthly")
    def monthly_comparison():
        """
        Aggregates totals per month. Income is the sum of positive amounts,
        expense is the absolute sum of negative amounts, net is income + expense_signed.
        Optional query params:
          - start (YYYY-MM-DD)
          - end (YYYY-MM-DD)
          - client_id (int)
        """
        start, err = _parse_date("start")
        if err:
            return jsonify({"error": err}), 400
        end, err = _parse_date("end")
        if err:
            return jsonify({"error": err}), 400

        client_id_raw = request.args.get("client_id")
        client_id = int(client_id_raw) if client_id_raw else None

        stmt = (
            select(
                func.strftime("%Y", Transaction.date_transaction).label("year"),
                func.strftime("%m", Transaction.date_transaction).label("month"),
                func.sum(
                    case((Transaction.montant >= 0, Transaction.montant), else_=0)
                ).label("income"),
                func.sum(
                    case((Transaction.montant < 0, Transaction.montant), else_=0)
                ).label("expense_signed"),
                func.sum(Transaction.montant).label("net"),
            )
            .group_by("year", "month")
            .order_by("year", "month")
        )
        stmt = _apply_common_filters(stmt, start, end, client_id)

        with Session(engine) as session:
            rows = session.exec(stmt).all()

        data = []
        for year, month, income, expense_signed, net in rows:
            data.append(
                {
                    "year": int(year),
                    "month": int(month),
                    "income": float(income or 0),
                    "expense": float(abs(expense_signed or 0)),
                    "net": float(net or 0),
                    "label": f"{year}-{str(month).zfill(2)}",
                }
            )
        return jsonify({"data": data})

    @app.get("/api/transactions/category-averages")
    def category_averages():
        """
        Average amount per category.
        Optional query params:
          - start (YYYY-MM-DD)
          - end (YYYY-MM-DD)
          - client_id (int)
        """
        start, err = _parse_date("start")
        if err:
            return jsonify({"error": err}), 400
        end, err = _parse_date("end")
        if err:
            return jsonify({"error": err}), 400

        client_id_raw = request.args.get("client_id")
        client_id = int(client_id_raw) if client_id_raw else None

        stmt = (
            select(
                Transaction.categorie,
                func.avg(Transaction.montant).label("average_amount"),
            )
            .group_by(Transaction.categorie)
            .order_by(Transaction.categorie)
        )
        stmt = _apply_common_filters(stmt, start, end, client_id)

        with Session(engine) as session:
            rows = session.exec(stmt).all()

        data = []
        for categorie, average in rows:
            data.append(
                {
                    "category": categorie,
                    "average": float(average or 0),
                }
            )
        return jsonify({"data": data})

    @app.post("/api/auth/login/client")
    def login_client():
        """Client login endpoint"""
        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        hashed_password = hash_mdp(password)

        with Session(engine) as db_session:
            # Find client login credentials
            login_stmt = select(Connexion_client).where(Connexion_client.email == email)
            login_cred = db_session.exec(login_stmt).first()

            if not login_cred or login_cred.mot_de_passe != hashed_password:
                return jsonify({"error": "Invalid email or password"}), 401

            # Get full client information
            client_stmt = select(Client).where(Client.client_id == login_cred.client_id)
            client = db_session.exec(client_stmt).first()

            if not client:
                return jsonify({"error": "Client not found"}), 404

            # Set session
            session["user_type"] = "client"
            session["user_id"] = client.client_id
            session["email"] = client.email

            return jsonify({
                "success": True,
                "user": {
                    "id": client.client_id,
                    "firstName": client.prenom,
                    "lastName": client.nom,
                    "email": client.email,
                    "phone": client.telephone,
                    "profession": client.profession,
                    "address": client.adresse,
                    "accountNumber": client.numero_compte,
                    "balance": float(client.solde_initial),
                    "avatar": f"{client.prenom[0]}{client.nom[0]}".upper()
                }
            })

    @app.post("/api/auth/login/admin")
    def login_admin():
        """Admin login endpoint"""
        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        hashed_password = hash_mdp(password)

        with Session(engine) as db_session:
            admin_stmt = select(Administrateur).where(Administrateur.email == email)
            admin = db_session.exec(admin_stmt).first()

            if not admin or admin.mot_de_passe != hashed_password:
                return jsonify({"error": "Invalid email or password"}), 401

            # Set session
            session["user_type"] = "admin"
            session["user_id"] = admin.id
            session["email"] = admin.email

            return jsonify({
                "success": True,
                "user": {
                    "id": admin.id,
                    "name": admin.nom,
                    "email": admin.email,
                    "role": admin.role,
                    "avatar": "AD"
                }
            })

    @app.post("/api/auth/logout")
    def logout():
        """Logout endpoint"""
        session.clear()
        return jsonify({"success": True, "message": "Logged out successfully"})

    @app.get("/api/auth/current-user")
    def get_current_user():
        """Get current logged-in user information"""
        user_type = session.get("user_type")
        user_id = session.get("user_id")

        if not user_type or not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        with Session(engine) as db_session:
            if user_type == "client":
                client_stmt = select(Client).where(Client.client_id == user_id)
                client = db_session.exec(client_stmt).first()
                if not client:
                    session.clear()
                    return jsonify({"error": "Client not found"}), 404

                return jsonify({
                    "userType": "client",
                    "user": {
                        "id": client.client_id,
                        "firstName": client.prenom,
                        "lastName": client.nom,
                        "email": client.email,
                        "phone": client.telephone,
                        "profession": client.profession,
                        "address": client.adresse,
                        "accountNumber": client.numero_compte,
                        "balance": float(client.solde_initial),
                        "avatar": f"{client.prenom[0]}{client.nom[0]}".upper()
                    }
                })
            else:  # admin
                admin_stmt = select(Administrateur).where(Administrateur.id == user_id)
                admin = db_session.exec(admin_stmt).first()
                if not admin:
                    session.clear()
                    return jsonify({"error": "Admin not found"}), 404

                return jsonify({
                    "userType": "admin",
                    "user": {
                        "id": admin.id,
                        "name": admin.nom,
                        "email": admin.email,
                        "role": admin.role,
                        "avatar": "AD"
                    }
                })

    @app.post("/api/credit-request")
    def submit_credit_request():
        """Submit a credit request"""
        user_type = session.get("user_type")
        user_id = session.get("user_id")

        if user_type != "client":
            return jsonify({"error": "Only clients can submit credit requests"}), 403

        data = request.get_json()
        amount = data.get("amount")
        duration = data.get("duration")
        purpose = data.get("purpose")

        if not amount or not duration or not purpose:
            return jsonify({"error": "Amount, duration, and purpose are required"}), 400

        # Store credit request (in a real app, you'd have a CreditRequest table)
        # For now, we'll return success and the request details
        return jsonify({
            "success": True,
            "message": "Credit request submitted successfully",
            "request": {
                "clientId": user_id,
                "amount": float(amount),
                "duration": int(duration),
                "purpose": purpose,
                "status": "pending"
            }
        })

    @app.post("/api/chat/predict")
    def chat_predict():
        """AI chat endpoint for banking predictions based on credit request"""
        user_type = session.get("user_type")
        user_id = session.get("user_id")

        if user_type != "client":
            return jsonify({"error": "Only clients can use the chat"}), 403

        data = request.get_json()
        message = data.get("message", "").strip()
        credit_amount = data.get("creditAmount")
        credit_duration = data.get("creditDuration")

        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Get client's financial data for context
        with Session(engine) as db_session:
            client_stmt = select(Client).where(Client.client_id == user_id)
            client = db_session.exec(client_stmt).first()

            if not client:
                return jsonify({"error": "Client not found"}), 404

            # Calculate average monthly transactions
            trans_stmt = select(
                func.avg(Transaction.montant).label("avg_amount"),
                func.count(Transaction.id_transaction).label("count")
            ).where(Transaction.id_client == user_id)
            trans_result = db_session.exec(trans_stmt).first()

            avg_transaction = float(trans_result[0] or 0) if trans_result else 0
            transaction_count = trans_result[1] if trans_result else 0

        # Simple AI-like prediction logic based on client data
        message_lower = message.lower()
        response = ""

        if any(word in message_lower for word in ["crédit", "prêt", "loan", "credit"]):
            if credit_amount and credit_duration:
                monthly_payment = float(credit_amount) / int(credit_duration)
                balance = float(client.solde_initial)

                if balance > monthly_payment * 3:
                    response = f"Basé sur votre solde actuel ({balance:,.0f} FCFA) et votre demande de crédit ({credit_amount:,.0f} FCFA sur {credit_duration} mois), votre profil semble favorable. La mensualité estimée serait d'environ {monthly_payment:,.0f} FCFA, ce qui représente un ratio d'endettement raisonnable."
                else:
                    response = f"Votre demande de crédit nécessite une analyse approfondie. Avec un solde de {balance:,.0f} FCFA, il serait recommandé d'augmenter votre épargne avant de contracter un crédit de {credit_amount:,.0f} FCFA."
            else:
                response = "Pour une analyse précise de votre demande de crédit, veuillez fournir le montant et la durée souhaités."
        elif any(word in message_lower for word in ["solde", "balance", "compte"]):
            response = f"Votre solde actuel est de {client.solde_initial:,.0f} FCFA. Vous avez effectué {transaction_count} transaction(s) avec une moyenne de {avg_transaction:,.0f} FCFA par transaction."
        elif any(word in message_lower for word in ["éligibilité", "eligible", "score"]):
            # Simple eligibility calculation
            balance = float(client.solde_initial)
            if balance > 1000000:
                score = 9.0
            elif balance > 500000:
                score = 7.5
            else:
                score = 6.0

            response = f"Basé sur votre profil financier, votre score d'éligibilité estimé est de {score}/10. Votre solde actuel de {balance:,.0f} FCFA et votre historique de transactions sont pris en compte dans cette évaluation."
        else:
            response = "Je peux vous aider avec des questions sur votre crédit, votre solde, votre éligibilité, ou d'autres aspects de vos finances. Posez-moi une question spécifique !"

        return jsonify({
            "success": True,
            "response": response,
            "context": {
                "balance": float(client.solde_initial),
                "avgTransaction": avg_transaction,
                "transactionCount": transaction_count
            }
        })

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/")
    def index():
        return send_from_directory(".", "main.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)


