from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
import plotly.io as pio
from polaczenie_db import get_engine

# Inicjalizacja aplikacji Flask
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    """
    Główna funkcja obsługująca zapytania do strony głównej aplikacji.
    Wyświetla dane COVID-19 w formie tabeli, wykresu słupkowego oraz mapy.
    Użytkownik może filtrować dane według roku i kraju.
    """
    engine = get_engine()

    # Pobranie listy unikalnych lat, dla których dostępne są dane
    with engine.connect() as conn:
        lata_query = """
        SELECT DISTINCT EXTRACT(YEAR FROM updated) AS rok
        FROM covid19_dane_tabela
        WHERE updated IS NOT NULL
        ORDER BY rok DESC
        """
        lata_df = pd.read_sql(lata_query, conn)
        lata = lata_df["rok"].dropna().astype(int).tolist()

    # Wybór domyślnego roku (w tym przypadku ustawiony 2020r.)
    default_year = 2020 if 2020 in lata else (lata[0] if lata else 2020)
    selected_year = request.args.get("rok", str(default_year))
    if selected_year not in map(str, lata):
        selected_year = str(default_year)

    # Wybór kraju (domyślnie wszystkie kraje)
    selected_country = request.args.get("kraj", "Wszystkie kraje")

    # Pobranie najnowszego rekordu dla każdego kraju z wybranego roku
    with engine.connect() as conn:
        query = f"""
        SELECT DISTINCT ON (country_region) 
               country_region, confirmed, deaths, recovered,
               latitude, longitude, updated
        FROM covid19_dane_tabela
        WHERE confirmed IS NOT NULL 
          AND deaths IS NOT NULL
          AND recovered IS NOT NULL
          AND latitude IS NOT NULL
          AND longitude IS NOT NULL
          AND EXTRACT(YEAR FROM updated) = {selected_year}
        ORDER BY country_region, updated DESC
        """
        df = pd.read_sql(query, conn)

    def safe_percent(part, whole):
        """
        Funkcja służąca do obliczania procentowej wartości udziału `part` w `whole`.
        Zabezpiecza przed dzieleniem przez zero.
        """
        return round((part / whole) * 100, 2) if whole and whole > 0 else 0

    # Obliczenie procentów zgonów i wyzdrowień
    df["% zgonów"] = df.apply(lambda row: safe_percent(row["deaths"], row["confirmed"]), axis=1)
    df["% wyzdrowień"] = df.apply(lambda row: safe_percent(row["recovered"], row["confirmed"]), axis=1)

    # Sortowanie danych według liczby potwierdzonych przypadków
    df = df.sort_values(by="confirmed", ascending=False)

    # Lista krajów do wyboru w formularzu
    kraje = ["Wszystkie kraje"] + sorted(df["country_region"].unique())
    if selected_country != "Wszystkie kraje":
        df = df[df["country_region"] == selected_country]

    # Przygotowanie danych do wykresu słupkowego (zakażenia, zgony, wyzdrowienia)
    df_melt = df.melt(
        id_vars=["country_region"],
        value_vars=["confirmed", "deaths", "recovered"],
        var_name="Rodzaj", value_name="Liczba"
    )
    mapping = {"confirmed": "Zakażenia", "deaths": "Zgony", "recovered": "Wyzdrowienia"}
    df_melt["Rodzaj"] = df_melt["Rodzaj"].map(mapping)

    color_map = {
        "Zakażenia": "#f9c49a",
        "Zgony": "#f4a6a6",
        "Wyzdrowienia": "#a8e6a1"
    }

    # Tworzenie wykresu słupkowego
    fig_bar = px.bar(
        df_melt,
        x="country_region",
        y="Liczba",
        color="Rodzaj",
        barmode="group",
        title=f"Porównanie zakażeń, zgonów i wyzdrowień w roku {selected_year}",
        labels={"country_region": "Kraj"},
        color_discrete_map=color_map
    )
    fig_bar.update_layout(
        plot_bgcolor="#fff0f5",
        paper_bgcolor="#fff0f5",
        font=dict(family="Verdana", size=14),
        title_font_size=24,
        legend_title_text=""
    )
    wykres_slupkowy = pio.to_html(fig_bar, full_html=False)

    # Tworzenie wykresu mapy geograficznej z lokalizacją zakażeń
    fig_map = px.scatter_geo(
        df,
        lat="latitude",
        lon="longitude",
        size="confirmed",
        color="confirmed",
        hover_name="country_region",
        projection="natural earth",
        title=f"Rozmieszczenie zakażeń na mapie – {selected_year}",
        color_continuous_scale=px.colors.sequential.Pinkyl
    )
    fig_map.update_layout(
        plot_bgcolor="#fff0f5",
        paper_bgcolor="#fff0f5",
        font=dict(family="Verdana", size=14),
        title_font_size=24,
        coloraxis_colorbar=dict(title="Zakażenia")
    )
    wykres_mapa = pio.to_html(fig_map, full_html=False)

    # Konwersja danych do formatu słownikowego dla tabeli HTML
    tabela = df.to_dict(orient="records")

    # Renderowanie szablonu HTML z danymi i wykresami
    return render_template(
        "index.html",
        tabela=tabela,
        wykres_slupkowy=wykres_slupkowy,
        wykres_mapa=wykres_mapa,
        kraje=kraje,
        selected_country=selected_country,
        selected_year=selected_year,
        lata=lata
    )

# Uruchomienie aplikacji w trybie debugowania
if __name__ == "__main__":
    app.run
