from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Tuple

from flask import Flask, jsonify, request, send_from_directory
from sqlalchemy import case, func
from sqlmodel import Session, select

from tables__projet import Transaction, create_db_and_table, engine


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


