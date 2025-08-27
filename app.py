import dash
from dash import dcc, html, Input, Output
from pathlib import Path
import requests
import plotly.graph_objs as go
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px


url = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
p = Path("db/Chinook.sqlite")
p.write_bytes(requests.get(url, timeout=60).content)

engine = create_engine(f"sqlite:///{p.as_posix()}")


# Consulta
query = f'''
SELECT 
  t.Name AS TrackName, 
  ar.Name AS ArtistName, 
  a.Title AS AlbumTitle, 
  COALESCE(t.Composer, 'unknown') AS composer, 
  g.Name AS Genre,
  COUNT(il.TrackId) AS quantity, 
  COALESCE(SUM(il.UnitPrice), 0) AS total_income,
  COUNT(pt.TrackId) AS popularity

FROM Track t
LEFT JOIN Genre g   ON t.GenreId = g.GenreId 
LEFT JOIN Album a   ON t.AlbumId = a.AlbumId
LEFT JOIN Artist ar ON a.ArtistId = ar.ArtistId
LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
LEFT JOIN Invoice i ON i.InvoiceId = il.InvoiceId
LEFT JOIN PlaylistTrack pt ON pt.TrackId = t.TrackId
GROUP BY t.Name, ar.Name, a.Title, t.Composer, g.Name
ORDER BY total_income DESC

'''

df= pd.read_sql(query, engine)

# ==== App Setup ====
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Chinook Dashboard"

app.layout = html.Div([

    # Header
    html.Div([
        html.H1("🎧 Dashboard de preferencias musicales", style={"marginBottom": "0"}),
        html.H4("Chinook DB", style={"marginTop": "0", "color": "gray"}),
        html.Label("Es este dashboard puedes explorar las preferencias musicales de los clientes de una tienda de música digital. Usa los filtros para analizar diferentes géneros y artistas, y observa cómo varían los ingresos, ventas y popularidad.", style={"marginTop": "10px", "color": "black"}),
    ], style={"padding": "20px"}),

    # Body layout
    html.Div([

        # Sidebar
        html.Div([
            html.H5("Filtros"),
            html.Label("Género", style={"marginTop": "15px"}),
            dcc.Dropdown(
                id="genre-dd",
                options=df["Genre"].unique(),
                value=df["Genre"].unique()[3:7], 
                multi=True,
                placeholder="Select genre(s)",
                searchable=True
            ),
            html.Label("Artista", style={"marginTop": "15px"}),
            dcc.Dropdown(
                id="artist-dd",
                options=df["ArtistName"].unique(),
                value=[], 
                multi=True,
                placeholder="Select artist(s)",
                searchable=True
            ),
        ], style={
            "width": "20%", "padding": "20px", "backgroundColor": "#f7f7f7"
        }),

        # Main content
        html.Div([

            # Metrics
            html.Div([
                html.Div(id="card1", className="card"),
                html.Div(id="card2", className="card"),
                html.Div(id="card3", className="card")
            ], style={"display": "flex", "gap": "20px", "marginBottom": "20px"}),

            # Graphs
            html.Div([
                dcc.Graph(id="fig2", style={"flex": 1})
            ], style={"display": "flex", "gap": "20px"}),

            html.Div([
                dcc.Graph(id="fig1", style={"flex": 1}),
            ], style={"display": "flex", "gap": "20px"})
        ], style={"width": "80%", "padding": "20px"})
    ], style={"display": "flex"})

], style={"fontFamily": "Arial, sans-serif"})

# ==== Callbacks ====
@app.callback(
    Output("card1", "children"),
    Output("card2", "children"),
    Output("card3", "children"),
    Output("fig1", "figure"),
    Output("fig2", "figure"),
    Input("genre-dd", "value"),
    Input("artist-dd", "value"),
)

def update_dashboard(genres, artists):

    # Filtrado
    dff = df[(df["Genre"].isin(genres)) | (df["ArtistName"].isin(artists))]

    # Cards
    total_income = dff["total_income"].sum()
    tracks_sold = dff["quantity"].sum()
    popularity = dff["popularity"].mean()

    card1 = html.Div([
        html.H6("Ingresos Generados", style={"color": "gray"}),
        html.H3(f"{total_income:.2f} USD")
    ], style={"padding": "20px", "backgroundColor": "#ffffff", "borderRadius": "8px", "boxShadow": "0 0 5px #ccc"})

    card2 = html.Div([
        html.H6("Tracks Vendidos", style={"color": "gray"}),
        html.H3(f"{tracks_sold:.1f} tracks")
    ], style={"padding": "20px", "backgroundColor": "#ffffff", "borderRadius": "8px", "boxShadow": "0 0 5px #ccc"})

    card3 = html.Div([
        html.H6("Popularidad Promedio", style={"color": "gray"}),
        html.H3(f"{popularity:.1f} playlists")
    ], style={"padding": "20px", "backgroundColor": "#ffffff", "borderRadius": "8px", "boxShadow": "0 0 5px #ccc"})

    # Figures

    group_genre= dff.groupby('Genre').agg({'total_income':'sum', 'popularity':'mean'}).reset_index()
    group_artist= dff.groupby('ArtistName').agg({'total_income':'sum'}).reset_index()

    fig1 = px.bar(group_genre.sort_values('total_income', ascending=False), x="Genre", y="total_income", title="Ventas totales por Géneros")
    fig2 = px.bar(group_artist.sort_values('total_income', ascending=False), x="ArtistName", y="total_income",  title="Ventas totales por Artistas")

    return card1, card2, card3, fig1, fig2

# ==== Run ====

if __name__ == "__main__":
    app.run_server(debug=True)