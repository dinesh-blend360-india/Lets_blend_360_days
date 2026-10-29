from flask import Flask, render_template, jsonify
import psycopg2
import os

app = Flask(__name__)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "retail_sales"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        port=os.getenv("DB_PORT", "5432")
    )


def get_kpis():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COALESCE(SUM(amount), 0) AS total_revenue,
            COUNT(DISTINCT order_id) AS total_orders,
            COALESCE(SUM(qty), 0) AS total_units,
            ROUND(
                COALESCE(SUM(amount), 0) /
                NULLIF(COUNT(DISTINCT order_id), 0),
                2
            ) AS average_order_value
        FROM sales;
    """)

    total_revenue, total_orders, total_units, average_order_value = cursor.fetchone()

    cursor.execute("""
        SELECT
            ROUND(
                100.0 *
                COUNT(DISTINCT CASE
                    WHEN UPPER(order_status) LIKE '%CANCEL%'
                    THEN order_id
                END)
                /
                NULLIF(COUNT(DISTINCT order_id), 0),
                2
            )
        FROM sales;
    """)

    cancellation_rate = cursor.fetchone()[0]

    cursor.execute("""
        SELECT region
        FROM sales
        GROUP BY region
        ORDER BY SUM(amount) DESC
        LIMIT 1;
    """)

    top_region = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return {
        "total_revenue": float(total_revenue),
        "total_orders": int(total_orders),
        "total_units": int(total_units),
        "average_order_value": float(average_order_value),
        "cancellation_rate": float(cancellation_rate),
        "top_region": top_region
    }


@app.route("/")
def index():
    kpis = get_kpis()
    return render_template("index.html", kpis=kpis)


@app.route("/api/kpis")
def api_kpis():
    return jsonify(get_kpis())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)