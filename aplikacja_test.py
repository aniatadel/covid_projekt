from flask import Flask, render_template
import pandas as pd
import plotly.express as px
import plotly.io as pio
from polaczenie_db import get_connection

app = Flask(__name__)

@app.route("/")
def index():
    conn = get_connection()
    query = "SELECT * FROM covid19_dane_tabela LIMIT 100"
    df = pd.read_sql(query, conn)
    conn.close()

    # Grupowanie zakażeń wg kraju
    df_grouped = df.groupby("country_region")["confirmed"].sum().reset_index()
    df_grouped = df_grouped.sort_values(by="confirmed", ascending=False).head(10)

    # Wykres
    fig = px.bar(df_grouped, x="country_region", y="confirmed", title="Top 10 krajów – liczba zakażeń")
    chart_html = pio.to_html(fig, full_html=False)

    # Przekazanie danych do szablonu
    return render_template("index.html", tabela=df.head(20).to_dict(orient="records"), wykres=chart_html)

if __name__ == "__main__":
    app.run(debug=True)
