"""ArtizBoard — Seed Pages d'Établissement

Idempotent. Usage: python seed_pages.py
"""
import sys, uuid, logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import psycopg2
from ArtizBoardCommon.config_loader import get_db_config

logging.basicConfig(level=logging.INFO, format="[seed-pages] %(message)s")
log = logging.getLogger("seed-pages")

db = get_db_config()
conn = psycopg2.connect(host=db[0], port=db[1], dbname=db[2],
                        user=db[3], password=db[4], client_encoding="UTF8")
conn.autocommit = False
cur = conn.cursor()

# Récupérer l'établissement et l'admin
cur.execute("SELECT id FROM etablissements WHERE deleted_at IS NULL LIMIT 1")
eid = cur.fetchone()[0]
cur.execute("SELECT id FROM utilisateurs WHERE deleted_at IS NULL ORDER BY created_at LIMIT 1")
uid = cur.fetchone()[0]

log.info(f"Établissement: {eid}")
log.info(f"Admin: {uid}")

# Nettoyer les anciennes pages
cur.execute("DELETE FROM pages_etablissement WHERE etablissement_id = %s", (eid,))
conn.commit()

PAGES = [
    {
        "numero_page": 1,
        "titre": "Galerie du Restaurant",
        "contenu_html": """<h2>Notre Restaurant en Images</h2>
<p>Plongez dans l'ambiance chaleureuse du Restaurant La République à travers notre galerie photo.</p>

<div class="gallery">
  <div class="gallery-item">
    <img src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=300&fit=crop" alt="Salle principale">
    <span>Salle principale — élégance et confort</span>
  </div>
  <div class="gallery-item">
    <img src="https://images.unsplash.com/photo-1559339352-11d035aa65de?w=400&h=300&fit=crop" alt="Terrasse">
    <span>Terrasse ombragée — idéale pour vos soirées</span>
  </div>
  <div class="gallery-item">
    <img src="https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=400&h=300&fit=crop" alt="Bar">
    <span>Bar — cocktails et saveurs locales</span>
  </div>
  <div class="gallery-item">
    <img src="https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400&h=300&fit=crop" alt="Cuisine">
    <span>Cuisine ouverte — transparence et qualité</span>
  </div>
  <div class="gallery-item">
    <img src="https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400&h=300&fit=crop" alt="Plat signature">
    <span>Notre plat signature — Thieboudiene Royal</span>
  </div>
  <div class="gallery-item">
    <img src="https://images.unsplash.com/photo-1552566626-52f8b828add9?w=400&h=300&fit=crop" alt="Événement">
    <span>Soirée privée — anniversaires et fêtes</span>
  </div>
</div>

<p class="cta">Vous aussi, vivez l'expérience La République. Réservez votre table dès maintenant !</p>""",
        "contenu_css": """.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin: 24px 0;
}
.gallery-item {
  background: #f5f5f5;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}
.gallery-item:hover {
  transform: scale(1.02);
}
.gallery-item img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  display: block;
}
.gallery-item span {
  display: block;
  padding: 12px;
  font-size: 14px;
  color: #333;
  text-align: center;
}
.cta {
  text-align: center;
  font-size: 18px;
  color: #1a6d4a;
  font-weight: bold;
  margin-top: 32px;
}
""",
        "est_active": True,
    },
    {
        "numero_page": 2,
        "titre": "Galerie de la Boutique",
        "contenu_html": """<h2>Notre Boutique</h2>
<p>Découvrez notre sélection de produits artisanaux et gastronomiques.</p>

<div class="shop-gallery">
  <div class="shop-item">
    <img src="https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&h=300&fit=crop" alt="Épices locales">
    <div class="shop-info">
      <h3>Épices locales</h3>
      <p>Piment, gingembre, curcuma — pure saveur d'Afrique</p>
    </div>
  </div>
  <div class="shop-item">
    <img src="https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&h=300&fit=crop" alt="Huiles artisanales">
    <div class="shop-info">
      <h3>Huiles artisanales</h3>
      <p>Huile de palme rouge, beurre de karité, huile de coco</p>
    </div>
  </div>
  <div class="shop-item">
    <img src="https://images.unsplash.com/photo-1588964895597-cfccd6e2dbf9?w=400&h=300&fit=crop" alt="Paniers cadeaux">
    <div class="shop-info">
      <h3>Paniers cadeaux</h3>
      <p>Assortiment de produits locaux dans un panier tressé</p>
    </div>
  </div>
</div>

<p class="note">📍 Retrouvez notre boutique au sein du restaurant — ouvert du lundi au samedi, 10h - 21h.</p>""",
        "contenu_css": """.shop-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  margin: 24px 0;
}
.shop-item {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.shop-item img {
  width: 100%;
  height: 220px;
  object-fit: cover;
}
.shop-info {
  padding: 16px;
}
.shop-info h3 {
  margin: 0 0 6px 0;
  color: #1a1a2e;
  font-size: 18px;
}
.shop-info p {
  margin: 0;
  color: #666;
  font-size: 14px;
}
.note {
  text-align: center;
  color: #555;
  font-style: italic;
  margin-top: 24px;
  padding: 16px;
  background: #fef9e6;
  border-radius: 8px;
}
""",
        "est_active": True,
    },
    {
        "numero_page": 3,
        "titre": "Cafétéria Ouverte 24/24",
        "contenu_html": """<div class="hero-banner">
  <h1>☕ Ouvert 24h/24 — 7j/7</h1>
  <p>La seule cafétéria du quartier qui ne dort jamais</p>
</div>

<h2>Pourquoi nous choisir ?</h2>

<div class="features">
  <div class="feature">
    <span class="icon">🕐</span>
    <h3>Disponibilité permanente</h3>
    <p>Que ce soit à 6h du matin pour un café avant le travail ou à 3h du matin après une soirée, nous sommes là.</p>
  </div>
  <div class="feature">
    <span class="icon">🌙</span>
    <h3>Ambiance nocturne</h3>
    <p>Un espace calme et lumineux pour travailler, lire ou simplement profiter d'un moment de tranquillité.</p>
  </div>
  <div class="feature">
    <span class="icon">🥐</span>
    <h3>Service continu</h3>
    <p>Carte complète disponible 24h/24 : petit-déjeuner, déjeuner, dîner et collations tardives.</p>
  </div>
</div>

<div class="stats">
  <div class="stat">
    <span class="stat-number">365</span>
    <span class="stat-label">Jours par an</span>
  </div>
  <div class="stat">
    <span class="stat-number">24</span>
    <span class="stat-label">Heures par jour</span>
  </div>
  <div class="stat">
    <span class="stat-number">1</span>
    <span class="stat-label">An d'ouverture continue</span>
  </div>
</div>

<p class="signature">Depuis 1 an, nous n'avons jamais fermé nos portes. Un record dont nous sommes fiers !</p>""",
        "contenu_css": """.hero-banner {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: white;
  text-align: center;
  padding: 40px 20px;
  border-radius: 16px;
  margin-bottom: 32px;
}
.hero-banner h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
}
.hero-banner p {
  margin: 0;
  opacity: 0.85;
  font-size: 16px;
}
.features {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin: 24px 0;
}
.feature {
  background: #f8f9fa;
  padding: 24px;
  border-radius: 12px;
  text-align: center;
  border-left: 4px solid #e67e22;
}
.feature .icon {
  font-size: 36px;
}
.feature h3 {
  margin: 12px 0 8px 0;
  color: #1a1a2e;
}
.feature p {
  margin: 0;
  color: #666;
  font-size: 14px;
}
.stats {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin: 32px 0;
  padding: 24px;
  background: linear-gradient(135deg, #e67e22, #f39c12);
  border-radius: 12px;
  color: white;
  text-align: center;
}
.stat-number {
  display: block;
  font-size: 36px;
  font-weight: bold;
}
.stat-label {
  display: block;
  font-size: 14px;
  opacity: 0.9;
}
.signature {
  text-align: center;
  font-style: italic;
  color: #555;
  padding: 16px;
  border-top: 1px solid #eee;
  margin-top: 24px;
}
""",
        "est_active": True,
    },
    {
        "numero_page": 4,
        "titre": "Contact — Entreprises & Communauté",
        "contenu_html": """<h2>Contactez-nous</h2>
<p>Que vous soyez une entreprise, une association ou un particulier, nous sommes à votre écoute.</p>

<div class="contact-grid">
  <div class="contact-card">
    <div class="card-icon">📍</div>
    <h3>Adresse</h3>
    <p>123 Avenue de la République<br>Lomé, Togo</p>
  </div>
  <div class="contact-card">
    <div class="card-icon">📞</div>
    <h3>Téléphone</h3>
    <p>+228 90 00 00 01<br>+228 90 00 00 02</p>
  </div>
  <div class="contact-card">
    <div class="card-icon">📧</div>
    <h3>Email</h3>
    <p>contact@larepublique.tg<br>evenements@larepublique.tg</p>
  </div>
  <div class="contact-card">
    <div class="card-icon">🕐</div>
    <h3>Horaires</h3>
    <p>Lun-Jeu: 11h-22h<br>Ven-Sam: 11h-23h30<br>Dim: 12h-21h</p>
  </div>
</div>

<h2>Partenariats & Événements</h2>
<p>Nous travaillons avec les entreprises locales et les associations pour organiser :</p>
<ul class="services">
  <li><strong>Séminaires</strong> — salle privée équipée (vidéoprojecteur, wifi, sonorisation)</li>
  <li><strong>Team building</strong> — ateliers cuisine, dégustations, jeux</li>
  <li><strong>Réceptions privées</strong> — anniversaires, mariages, cocktail d'entreprise</li>
  <li><strong>Livraison entreprise</strong> — formule repas pour vos équipes (dès 10 personnes)</li>
</ul>

<div class="cta-contact">
  <h3>📩 Demande de devis</h3>
  <p>Pour toute demande de partenariat ou d'événement, contactez notre équipe commerciale :</p>
  <p><strong>Email :</strong> entreprises@larepublique.tg<br><strong>Tél :</strong> +228 90 00 00 03</p>
</div>

<h2>Ils nous font confiance</h2>
<div class="logos">
  <span class="logo-item">🏢 Groupe Togocom</span>
  <span class="logo-item">🏦 Banque Atlantique</span>
  <span class="logo-item">🏨 Hôtel 2 Février</span>
  <span class="logo-item">🌍 ONG Plan Togo</span>
</div>""",
        "contenu_css": """.contact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin: 24px 0;
}
.contact-card {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  border: 1px solid #eee;
}
.contact-card .card-icon {
  font-size: 32px;
  margin-bottom: 8px;
}
.contact-card h3 {
  margin: 0 0 8px 0;
  color: #1a1a2e;
  font-size: 16px;
}
.contact-card p {
  margin: 0;
  color: #666;
  font-size: 14px;
}
.services {
  list-style: none;
  padding: 0;
  margin: 16px 0;
}
.services li {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  color: #444;
}
.services li:last-child {
  border-bottom: none;
}
.cta-contact {
  background: linear-gradient(135deg, #1a6d4a, #2ecc71);
  color: white;
  padding: 24px;
  border-radius: 12px;
  margin: 24px 0;
  text-align: center;
}
.cta-contact h3 {
  margin: 0 0 8px 0;
}
.cta-contact p {
  margin: 4px 0;
  opacity: 0.95;
}
.logos {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  margin: 16px 0;
}
.logo-item {
  background: #f8f9fa;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
  border: 1px solid #e0e0e0;
}
""",
        "est_active": True,
    },
]

for p in PAGES:
    pid = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO pages_etablissement
            (id, etablissement_id, numero_page, titre, contenu_html, contenu_css, est_active, ordre, created_by, updated_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (pid, eid, p["numero_page"], p["titre"], p["contenu_html"], p["contenu_css"],
          p["est_active"], p["numero_page"], uid, uid))
    log.info(f"  ✓ Page {p['numero_page']} : {p['titre']}")

conn.commit()
cur.close()
conn.close()
log.info("Terminé — 4 pages insérées.")
