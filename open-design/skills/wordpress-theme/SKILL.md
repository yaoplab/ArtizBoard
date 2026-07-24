# Skill: Thème WordPress ArtizBoard

## 0. Contexte

**Projet** : ArtizBoard
**Module** : `wp-content/themes/artizboard/` — site public
**Utilisateurs** : Clients (navigateur), Admin (déploiement)
**Dépendances** : Supabase, Hostinger, WordPress
**Prérequis** : Supabase sync actif, Hostinger configuré

## 1. Fonction Principale

### Type : Systeme Ferme

**Entrée** : Clés Supabase (anon_key) + thème PHP/JS
**Sortie** : Site WordPress déployé sur Hostinger
**Traitement** : PHP templates → JS Supabase SDK → rendu → FTP deploy


## When to apply
- Building the public client-facing website
- Creating WordPress templates that read from Supabase
- Implementing the design system in HTML/CSS/JS for the web
- Setting up the WordPress theme on Hostinger

## Architecture

```
┌────────────────────────────────────────────────┐
│              HOSTINGER (PHP/MySQL)              │
│  ┌──────────────────────────────────────────┐  │
│  │  WordPress + Thème custom                │  │
│  │  ┌────────────────────────────────────┐  │  │
│  │  │ Thème artizboard/                    │  │  │
│  │  │  ├─ style.css      → CSS tokens    │  │  │
│  │  │  ├─ functions.php  → Enqueue, menus │  │  │
│  │  │  ├─ header.php     → Nav + panier   │  │  │
│  │  │  ├─ footer.php     → Footer + JS    │  │  │
│  │  │  ├─ assets/                         │  │  │
│  │  │  │  ├─ js/config.js   → Supabase   │  │  │
│  │  │  │  ├─ js/api.js      → REST calls │  │  │
│  │  │  │  ├─ js/cart.js     → localStorage│  │  │
│  │  │  │  └─ js/app.js      → Renderers  │  │  │
│  │  │  ├─ template-carte.php              │  │  │
│  │  │  ├─ template-apropos.php            │  │  │
│  │  │  └─ template-contact.php            │  │  │
│  │  └────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────┘  │
│              │ Supabase JS SDK                   │
└──────────────┼──────────────────────────────────┘
               ▼
┌────────────────────────────────────────────────┐
│              SUPABASE CLOUD                     │
│  /rest/v1/etablissements                       │
│  /rest/v1/produits?select=*,categories(nom)    │
│  /rest/v1/categories?etablissement_id=eq.xxx   │
│  /rest/v1/pages_etablissement?est_active=eq.true│
│  /rest/v1/faqs?etablissement_id=eq.xxx         │
│  /rest/v1/theme_config?etablissement_id=eq.xxx │
│  /rest/v1/commandes   (INSERT commands)         │
│  /rest/v1/lignes_commande (INSERT line items)   │
│  /storage/v1/object/public/* (images)           │
└────────────────────────────────────────────────┘
```

## Structure du thème — générer ces fichiers

### 1. `style.css` — Thème header + CSS Design System

```css
/*
Theme Name: ArtizBoard
Theme URI: https://artizboard.tg
Description: Thème WordPress pour établissements de restauration et boutique.
Version: 1.0
Author: ArtizBoard
License: MIT
Text Domain: artizboard
*/

/* === DESIGN TOKENS (M3 + Fibonacci) === */
:root {
  /* Couleurs */
  --primary: #1565C0;
  --on-primary: #FFFFFF;
  --primary-container: #BBDEFB;
  --primary-dark: #0D47A1;
  --secondary: #00897B;
  --secondary-container: #B2DFDB;
  --accent: #E65100;
  --accent-container: #FFCC80;
  --surface: #F5F7FA;
  --surface-variant: #E8EAF6;
  --background: #F5F7FA;
  --outline: #546E7A;
  --outline-variant: #B0BEC5;
  --text-strong: #1B1B1F;
  --text-soft: #455A64;
  --text-disabled: #90A4AE;
  --error: #C62828;
  --error-container: #FFCDD2;
  --success: #2E7D32;
  --success-container: #C8E6C9;

  /* Espacements Fibonacci × 4px */
  --space-xxs: 4px;
  --space-xs: 8px;
  --space-sm: 12px;
  --space-md: 20px;
  --space-lg: 32px;
  --space-xl: 52px;
  --space-xxl: 84px;

  /* Shapes */
  --shape-xs: 4px;
  --shape-sm: 8px;
  --shape-md: 12px;
  --shape-lg: 16px;
  --shape-xl: 28px;
  --shape-full: 9999px;

  /* Typographie */
  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --fs-display: 2.25rem;  /* 36px */
  --fs-headline: 1.5rem;  /* 24px */
  --fs-title: 1.25rem;    /* 20px */
  --fs-body: 0.875rem;    /* 14px */
  --fs-label: 0.75rem;    /* 12px */
  --fs-small: 0.6875rem;  /* 11px */

  --fw-bold: 700;
  --fw-medium: 500;
  --fw-regular: 400;

  --lh-tight: 1.25;
  --lh-normal: 1.5;
}

/* === RESET & BASE === */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; scroll-behavior: smooth; }
body {
  font-family: var(--font);
  font-size: var(--fs-body);
  line-height: var(--lh-normal);
  color: var(--text-strong);
  background: var(--background);
  -webkit-font-smoothing: antialiased;
}

/* === LAYOUT === */
.container { max-width: 960px; margin: 0 auto; padding: 0 var(--space-md); }
.page-content { min-height: 80vh; padding: var(--space-lg) 0; }
.section { padding: var(--space-lg) 0; }
.section-title { font-size: var(--fs-headline); font-weight: var(--fw-bold); margin-bottom: var(--space-md); color: var(--text-strong); }

/* === NAVIGATION === */
.nav { position: sticky; top: 0; z-index: 100; background: var(--surface); border-bottom: 1px solid var(--outline-variant); }
.nav-inner { display: flex; align-items: center; justify-content: space-between; padding: var(--space-sm) var(--space-md); max-width: 960px; margin: 0 auto; }
.nav-brand { font-size: var(--fs-title); font-weight: var(--fw-bold); color: var(--primary); text-decoration: none; display: flex; align-items: center; gap: var(--space-xs); }
.nav-brand img { width: 36px; height: 36px; border-radius: var(--shape-sm); }
.nav-links { display: flex; gap: var(--space-xs); align-items: center; }
.nav-link { padding: var(--space-sm) var(--space-md); border-radius: var(--shape-full); text-decoration: none; color: var(--text-soft); font-size: var(--fs-label); font-weight: var(--fw-medium); border: none; background: none; cursor: pointer; transition: background 0.2s; }
.nav-link:hover, .nav-link.active { background: var(--primary-container); color: var(--primary); }
.nav-cart { position: relative; }
.cart-badge { position: absolute; top: -4px; right: -4px; background: var(--accent); color: white; font-size: var(--fs-small); padding: 1px 6px; border-radius: var(--shape-full); min-width: 18px; text-align: center; font-weight: var(--fw-bold); }
.cart-badge.hidden { display: none; }

/* === HERO === */
.hero { background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); color: var(--on-primary); padding: var(--space-xl) var(--space-md); text-align: center; }
.hero-title { font-size: var(--fs-display); font-weight: var(--fw-bold); margin-bottom: var(--space-sm); }
.hero-subtitle { font-size: var(--fs-title); opacity: 0.85; margin-bottom: var(--space-lg); max-width: 600px; margin-left: auto; margin-right: auto; }

/* === BUTTONS === */
.btn { display: inline-flex; align-items: center; gap: var(--space-xs); padding: var(--space-sm) var(--space-md); border-radius: var(--shape-full); font-family: var(--font); font-size: var(--fs-label); font-weight: var(--fw-bold); cursor: pointer; border: none; text-decoration: none; transition: all 0.2s; line-height: 1; }
.btn-primary { background: var(--primary); color: var(--on-primary); }
.btn-primary:hover { background: var(--primary-dark); }
.btn-outline { background: transparent; border: 1px solid var(--primary); color: var(--primary); }
.btn-outline:hover { background: var(--primary-container); }
.btn-icon { background: none; border: none; cursor: pointer; font-size: 1.25rem; color: var(--text-soft); }
.btn-block { width: 100%; justify-content: center; }
.btn:disabled { opacity: 0.5; cursor: default; }

/* === CARDS === */
.card { background: var(--surface); border-radius: var(--shape-md); overflow: hidden; border: 1px solid var(--outline-variant); transition: box-shadow 0.2s; }
.card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.card-body { padding: var(--space-md); }
.card-title { font-size: var(--fs-title); font-weight: var(--fw-bold); color: var(--text-strong); margin-bottom: var(--space-xxs); }
.card-subtitle { font-size: var(--fs-label); color: var(--text-soft); }
.card-price { font-size: var(--fs-body); font-weight: var(--fw-bold); color: var(--primary); }

/* === PRODUCT GRID === */
.product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-md); }
.product-card { display: flex; padding: var(--space-md); gap: var(--space-md); align-items: center; background: var(--surface); border-radius: var(--shape-md); border: 1px solid var(--outline-variant); }
.product-card.in-cart { background: var(--primary-container); border-color: var(--primary); }
.product-image { width: 64px; height: 64px; border-radius: var(--shape-sm); object-fit: cover; background: var(--surface-variant); flex-shrink: 0; }
.product-info { flex: 1; }
.product-name { font-weight: var(--fw-bold); font-size: var(--fs-body); margin-bottom: 2px; }
.product-desc { font-size: var(--fs-small); color: var(--text-soft); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.product-price { font-size: var(--fs-title); font-weight: var(--fw-bold); color: var(--primary); }
.product-actions { display: flex; align-items: center; gap: var(--space-xs); flex-shrink: 0; }
.qty-btn { width: 28px; height: 28px; border-radius: var(--shape-full); border: 1px solid var(--primary); background: none; color: var(--primary); font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.qty-btn:hover { background: var(--primary-container); }
.qty-value { font-size: var(--fs-body); font-weight: var(--fw-bold); color: var(--primary); min-width: 20px; text-align: center; }

/* === CART DRAWER === */
.overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 200; }
.drawer { position: fixed; right: 0; top: 0; bottom: 0; width: 380px; max-width: 90vw; background: var(--surface); z-index: 201; display: flex; flex-direction: column; box-shadow: -4px 0 20px rgba(0,0,0,0.15); }
.drawer-header { display: flex; justify-content: space-between; align-items: center; padding: var(--space-md); border-bottom: 1px solid var(--outline-variant); }
.drawer-header h2 { font-size: var(--fs-title); font-weight: var(--fw-bold); }
.drawer-body { flex: 1; overflow-y: auto; padding: var(--space-md); }
.drawer-footer { padding: var(--space-md); border-top: 1px solid var(--outline-variant); }
.cart-total { display: flex; justify-content: space-between; font-weight: var(--fw-bold); margin-bottom: var(--space-sm); }
.cart-item { display: flex; justify-content: space-between; align-items: center; padding: var(--space-sm) 0; border-bottom: 1px solid var(--surface-variant); }
.cart-item-remove { font-size: 1.25rem; color: var(--error); cursor: pointer; background: none; border: none; padding: 4px; }

/* === CATEGORIES === */
.cat-list { display: flex; flex-direction: column; }
.cat-item { display: flex; justify-content: space-between; align-items: center; padding: var(--space-md); border-bottom: 1px solid var(--outline-variant); cursor: pointer; transition: background 0.2s; }
.cat-item:hover { background: var(--primary-container); }
.cat-item-name { font-size: var(--fs-title); font-weight: var(--fw-bold); }
.cat-item-count { font-size: var(--fs-label); color: var(--text-soft); background: var(--surface-variant); padding: 2px 10px; border-radius: var(--shape-full); }

/* === PAGES (À Propos) === */
.page-subnav { display: flex; gap: 0; overflow-x: auto; border-bottom: 2px solid var(--outline-variant); margin-bottom: var(--space-lg); }
.page-tab { padding: var(--space-sm) var(--space-md); font-size: var(--fs-label); font-weight: var(--fw-bold); color: var(--text-soft); background: none; border: none; border-bottom: 2px solid transparent; cursor: pointer; margin-bottom: -2px; white-space: nowrap; }
.page-tab.active { color: var(--primary); border-bottom-color: var(--primary); }

/* === FAQ === */
.faq-item { background: var(--surface); border-radius: var(--shape-sm); padding: var(--space-md); margin-bottom: var(--space-sm); border-left: 3px solid var(--primary); }
.faq-question { font-weight: var(--fw-bold); font-size: var(--fs-body); margin-bottom: var(--space-xxs); }
.faq-answer { font-size: var(--fs-label); color: var(--text-soft); }

/* === CONTACT === */
.contact-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--space-md); }
.contact-card { background: var(--surface); border-radius: var(--shape-md); padding: var(--space-md); text-align: center; border: 1px solid var(--outline-variant); }
.contact-icon { font-size: 2rem; margin-bottom: var(--space-xs); }
.contact-card h3 { font-size: var(--fs-body); font-weight: var(--fw-bold); margin-bottom: 4px; }
.contact-card p { font-size: var(--fs-label); color: var(--text-soft); }
.hours-table { width: 100%; border-collapse: collapse; }
.hours-table td { padding: var(--space-sm); border-bottom: 1px solid var(--outline-variant); font-size: var(--fs-body); }
.hours-table td:first-child { font-weight: var(--fw-bold); }
.hours-table td:last-child { text-align: right; color: var(--text-soft); }

/* === FOOTER === */
.footer { background: var(--surface); border-top: 1px solid var(--outline-variant); padding: var(--space-lg) var(--space-md); text-align: center; font-size: var(--fs-label); color: var(--text-soft); }
.footer-nav { display: flex; gap: var(--space-md); justify-content: center; margin-bottom: var(--space-sm); }
.footer-nav a { color: var(--text-soft); text-decoration: none; }
.footer-nav a:hover { color: var(--primary); }

/* === TOAST === */
.toast { position: fixed; bottom: var(--space-md); left: 50%; transform: translateX(-50%); background: var(--text-strong); color: white; padding: var(--space-sm) var(--space-md); border-radius: var(--shape-full); font-size: var(--fs-label); z-index: 300; box-shadow: 0 4px 12px rgba(0,0,0,0.3); animation: toast-in 0.3s ease; }
.toast.success { background: var(--success); }
.toast.error { background: var(--error); }
.toast.hidden { display: none; }
@keyframes toast-in { from { opacity: 0; transform: translateX(-50%) translateY(10px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }

/* === UTILS === */
.hidden { display: none !important; }
.text-center { text-align: center; }
.mt-lg { margin-top: var(--space-lg); }
.mb-md { margin-bottom: var(--space-md); }
.loading { text-align: center; padding: var(--space-xl); color: var(--text-soft); }
.empty-state { text-align: center; padding: var(--space-xl); color: var(--text-disabled); }
.empty-state-icon { font-size: 3rem; margin-bottom: var(--space-sm); opacity: 0.5; }

/* === RESPONSIVE === */
@media (max-width: 700px) {
  .nav-links { gap: 0; }
  .nav-link { padding: var(--space-sm); font-size: var(--fs-small); }
  .product-grid { grid-template-columns: 1fr; }
  .contact-grid { grid-template-columns: 1fr; }
  .hero { padding: var(--space-lg) var(--space-md); }
  .hero-title { font-size: 1.5rem; }
  .drawer { width: 100vw; max-width: 100vw; }
}
```

### 2. `functions.php` — WordPress setup

```php
<?php
/** ArtizBoard Theme Functions */

// Enqueue styles and scripts
function artizboard_enqueue() {
    wp_enqueue_style('artizboard-style', get_stylesheet_uri(), [], '1.0');
    wp_enqueue_style('artizboard-font', 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap', [], null);

    // Supabase SDK
    wp_enqueue_script('supabase-js', 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2', [], null, true);

    // App scripts
    wp_enqueue_script('artizboard-config', get_template_directory_uri() . '/assets/js/config.js', [], '1.0', true);
    wp_enqueue_script('artizboard-api', get_template_directory_uri() . '/assets/js/api.js', ['supabase-js', 'artizboard-config'], '1.0', true);
    wp_enqueue_script('artizboard-cart', get_template_directory_uri() . '/assets/js/cart.js', ['artizboard-api'], '1.0', true);
    wp_enqueue_script('artizboard-app', get_template_directory_uri() . '/assets/js/app.js', ['artizboard-cart'], '1.0', true);

    // Pass config to JS
    wp_localize_script('artizboard-config', 'wpArtizboard', [
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'templateUrl' => get_template_directory_uri(),
    ]);
}
add_action('wp_enqueue_scripts', 'artizboard_enqueue');

// Register menus
register_nav_menus([
    'primary' => 'Navigation principale',
    'footer' => 'Footer',
]);

// Theme support
add_theme_support('post-thumbnails');
add_theme_support('title-tag');
add_theme_support('html5', ['search-form', 'comment-form']);
```

### 3. `header.php` — Navigation + structure

```php
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<nav class="nav" id="siteNav">
    <div class="nav-inner">
        <a href="<?php echo home_url('/'); ?>" class="nav-brand" id="navBrand">
            🍽️ <?php bloginfo('name'); ?>
        </a>
        <div class="nav-links" id="navLinks">
            <button class="nav-link active" data-page="accueil">Accueil</button>
            <button class="nav-link" data-page="carte">🍽️ Carte</button>
            <button class="nav-link" data-page="apropos">ℹ️ À Propos</button>
            <button class="nav-link" data-page="contact">📞 Contact</button>
            <button class="nav-link nav-cart" id="cartBtn">
                🛒 <span class="cart-badge hidden" id="cartBadge">0</span>
            </button>
        </div>
    </div>
</nav>

<main class="page-content" id="mainContent">

<!-- WordPres default loop for static pages -->
<?php if (!is_page_template(['template-carte.php', 'template-apropos.php', 'template-contact.php'])): ?>
    <div class="container">
        <?php
        while (have_posts()):
            the_post();
            the_content();
        endwhile;
        ?>
    </div>
<?php endif; ?>
```

### 4. `footer.php` — Footer + cart drawer

```php
</main><!-- /#mainContent -->

<!-- Cart Drawer -->
<div class="overlay hidden" id="cartOverlay"></div>
<div class="drawer hidden" id="cartDrawer">
    <div class="drawer-header">
        <h2>🛒 Votre panier</h2>
        <button class="btn-icon" id="cartClose">✕</button>
    </div>
    <div class="drawer-body" id="cartItems"></div>
    <div class="drawer-footer">
        <div class="cart-total">
            <span>Total</span>
            <span id="cartTotal">0 FCFA</span>
        </div>
        <button class="btn btn-primary btn-block" id="checkoutBtn" disabled>
            Commander
        </button>
    </div>
</div>

<!-- Toast -->
<div class="toast hidden" id="toast"></div>

<footer class="footer">
    <div id="footerContent">
        <p>© <?php echo date('Y'); ?> <?php bloginfo('name'); ?></p>
    </div>
</footer>

<!-- Inline Init Script -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Determine current page from URL path or body class
    var path = window.location.pathname;
    var page = 'accueil';

    if (path.indexOf('/carte') !== -1) page = 'carte';
    else if (path.indexOf('/apropos') !== -1) page = 'apropos';
    else if (path.indexOf('/contact') !== -1) page = 'contact';

    if (typeof ArtizBoard !== 'undefined' && ArtizBoard.init) {
        ArtizBoard.init(page);
    }
});
</script>

<?php wp_footer(); ?>
</body>
</html>
```

### 5. `template-carte.php` — Page Carte / Menu

```php
<?php
/** Template Name: Carte / Menu */
get_header();
?>
<div class="container" id="carteContainer">
    <div class="section-title">Notre Carte</div>
    <div id="carteContent">
        <div class="loading">Chargement du menu...</div>
    </div>
</div>
<?php get_footer(); ?>
```

### 6. `template-apropos.php` — Page À Propos

```php
<?php
/** Template Name: À Propos */
get_header();
?>
<div class="container" id="aproposContainer">
    <div class="section-title">À Propos</div>
    <div id="aproposContent">
        <div class="loading">Chargement...</div>
    </div>
</div>
<?php get_footer(); ?>
```

### 7. `template-contact.php` — Page Contact

```php
<?php
/** Template Name: Contact */
get_header();
?>
<div class="container" id="contactContainer">
    <div class="section-title">Nous Contacter</div>
    <div id="contactContent">
        <div class="loading">Chargement...</div>
    </div>
</div>
<?php get_footer(); ?>
```

## JavaScript — assets/js/*

### `config.js` — Supabase configuration (MUST be customized)

```javascript
// Supabase Configuration
// Remplacer par les vraies valeurs de ton projet Supabase
const SUPABASE_URL = 'https://xxxxxxxxxxxx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Etablissement ID — récupéré dynamiquement au premier chargement
let ETABLISSEMENT_ID = null;

async function getEtablissementId() {
    if (ETABLISSEMENT_ID) return ETABLISSEMENT_ID;
    const { data } = await supabase
        .from('etablissements')
        .select('id')
        .limit(1)
        .single();
    if (data) ETABLISSEMENT_ID = data.id;
    return ETABLISSEMENT_ID;
}
```

### `api.js` — Supabase REST wrapper (MUST be customized)

```javascript
// API Wrapper for Supabase
// All data fetch functions

async function fetchEtablissement() {
    const { data } = await supabase
        .from('etablissements')
        .select('*')
        .limit(1)
        .single();
    return data;
}

async function fetchCategories(eid) {
    const { data } = await supabase
        .from('categories')
        .select('*')
        .eq('etablissement_id', eid)
        .order('nom');
    return data || [];
}

async function fetchProduits(eid) {
    const { data } = await supabase
        .from('produits')
        .select('*, categories!inner(nom)')
        .eq('etablissement_id', eid)
        .eq('permets_commande', true)
        .order('nom');
    return data || [];
}

async function fetchPages(eid) {
    const { data } = await supabase
        .from('pages_etablissement')
        .select('*')
        .eq('etablissement_id', eid)
        .eq('est_active', true)
        .order('ordre');
    return data || [];
}

async function fetchFAQs(eid) {
    const { data } = await supabase
        .from('faqs')
        .select('*')
        .eq('etablissement_id', eid)
        .order('ordre');
    return data || [];
}

async function fetchThemeConfig(eid) {
    const { data } = await supabase
        .from('theme_config')
        .select('*')
        .eq('etablissement_id', eid)
        .eq('est_actif', true)
        .limit(1)
        .single();
    return data;
}

async function submitCommande(commande, lignes) {
    const { data: cmdData, error: cmdError } = await supabase
        .from('commandes')
        .insert([commande])
        .select();
    if (cmdError) throw cmdError;
    
    const cmdId = cmdData[0].id;
    for (const ligne of lignes) {
        ligne.commande_id = cmdId;
    }
    const { error: lineError } = await supabase
        .from('lignes_commande')
        .insert(lignes);
    if (lineError) throw lineError;
    
    return cmdData[0];
}

// Helper: generate UUID v4
function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}
```

### `cart.js` — Panier localStorage (MUST be customized)

```javascript
// Cart Management — localStorage

const CART_KEY = 'artizboard_cart';

function getCart() {
    try {
        return JSON.parse(localStorage.getItem(CART_KEY)) || [];
    } catch { return []; }
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartUI();
}

function addToCart(produit) {
    const cart = getCart();
    const existing = cart.find(c => c.id === produit.id);
    if (existing) {
        existing.qte += 1;
    } else {
        cart.push({
            id: produit.id,
            nom: produit.nom,
            prix: parseFloat(produit.prix),
            qte: 1
        });
    }
    saveCart(cart);
}

function removeFromCart(produitId) {
    let cart = getCart();
    const item = cart.find(c => c.id === produitId);
    if (item) {
        item.qte -= 1;
        if (item.qte <= 0) cart = cart.filter(c => c.id !== produitId);
    }
    saveCart(cart);
}

function clearCart() {
    localStorage.removeItem(CART_KEY);
    updateCartUI();
}

function getCartTotal() {
    return getCart().reduce((sum, c) => sum + c.prix * c.qte, 0);
}

function getCartCount() {
    return getCart().reduce((sum, c) => sum + c.qte, 0);
}

function updateCartUI() {
    const cart = getCart();
    const count = getCartCount();
    const total = getCartTotal();
    
    const badge = document.getElementById('cartBadge');
    const cartBtn = document.getElementById('cartBtn');
    const checkoutBtn = document.getElementById('checkoutBtn');
    
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }
    if (checkoutBtn) checkoutBtn.disabled = count === 0;
    
    // Update cart drawer
    renderCartDrawer();
}

function renderCartDrawer() {
    const itemsEl = document.getElementById('cartItems');
    const totalEl = document.getElementById('cartTotal');
    if (!itemsEl || !totalEl) return;
    
    const cart = getCart();
    itemsEl.innerHTML = '';
    
    if (cart.length === 0) {
        itemsEl.innerHTML = '<div class="empty-state"><p>Votre panier est vide</p></div>';
        totalEl.textContent = '0 FCFA';
        return;
    }
    
    cart.forEach(item => {
        const div = document.createElement('div');
        div.className = 'cart-item';
        div.innerHTML = `
            <div>
                <div style="font-weight:600">${item.qte}× ${item.nom}</div>
                <div style="font-size:0.75rem;color:var(--text-soft)">${(item.prix * item.qte).toLocaleString()} FCFA</div>
            </div>
            <button class="cart-item-remove" data-id="${item.id}" title="Retirer">✕</button>
        `;
        itemsEl.appendChild(div);
    });
    
    totalEl.textContent = getCartTotal().toLocaleString() + ' FCFA';
    
    // Remove handlers
    itemsEl.querySelectorAll('.cart-item-remove').forEach(btn => {
        btn.addEventListener('click', function() {
            removeFromCart(this.dataset.id);
        });
    });
}

async function checkout() {
    const cart = getCart();
    if (cart.length === 0) return;
    
    const eid = await getEtablissementId();
    const total = getCartTotal();
    const tableParam = new URLSearchParams(window.location.search).get('table');
    const ref = tableParam || 'Web';
    
    const cmdId = uuidv4();
    const commande = {
        id: cmdId,
        etablissement_id: eid,
        reference_client: ref,
        type_service: 'sur_place',
        statut: 'en_attente',
        statut_paiement: 'en_attente',
        total: total,
        created_at: new Date().toISOString()
    };
    
    const lignes = cart.map(c => ({
        id: uuidv4(),
        commande_id: cmdId,
        produit_id: c.id,
        quantite: c.qte,
        prix_unitaire: c.prix
    }));
    
    try {
        await submitCommande(commande, lignes);
        clearCart();
        showToast('Commande enregistrée ! ✓', 'success');
    } catch (err) {
        showToast('Erreur: ' + err.message, 'error');
    }
}

// Cart drawer open/close
document.addEventListener('DOMContentLoaded', function() {
    const cartBtn = document.getElementById('cartBtn');
    const cartClose = document.getElementById('cartClose');
    const cartOverlay = document.getElementById('cartOverlay');
    const cartDrawer = document.getElementById('cartDrawer');
    const checkoutBtn = document.getElementById('checkoutBtn');
    
    function openCart() {
        cartOverlay.classList.remove('hidden');
        cartDrawer.classList.remove('hidden');
        renderCartDrawer();
    }
    function closeCart() {
        cartOverlay.classList.add('hidden');
        cartDrawer.classList.add('hidden');
    }
    
    if (cartBtn) cartBtn.addEventListener('click', openCart);
    if (cartClose) cartClose.addEventListener('click', closeCart);
    if (cartOverlay) cartOverlay.addEventListener('click', closeCart);
    if (checkoutBtn) checkoutBtn.addEventListener('click', function() {
        checkout().then(function() {
            closeCart();
        });
    });
});
```

### `app.js` — Initialisation et rendu (MUST be customized)

```javascript
// ArtizBoard — Main App Initializer & Renderers

const ArtizBoard = {
    etab: null,
    categories: [],
    produits: [],
    pages: [],
    faqs: [],
    themeConfig: null,
    activeTab: 0,

    async init(page) {
        this.activeTab = ['accueil','carte','apropos','contact'].indexOf(page);
        await this.loadData();
        this.applyThemeConfig();
        this.render();
        updateCartUI();
    },

    async loadData() {
        try {
            const eid = await getEtablissementId();
            const [etab, cats, prods, pages, faqs, themeConfig] = await Promise.all([
                fetchEtablissement(eid),
                fetchCategories(eid),
                fetchProduits(eid),
                fetchPages(eid),
                fetchFAQs(eid),
                fetchThemeConfig(eid)
            ]);
            this.etab = etab;
            this.categories = cats;
            this.produits = prods;
            this.pages = pages;
            this.faqs = faqs;
            this.themeConfig = themeConfig;
        } catch (e) {
            console.error('Load error:', e);
        }
    },

    applyThemeConfig() {
        if (!this.themeConfig) return;
        const root = document.documentElement;
        if (this.themeConfig.primary_color) root.style.setProperty('--primary', this.themeConfig.primary_color);
        if (this.themeConfig.secondary_color) root.style.setProperty('--secondary', this.themeConfig.secondary_color);
        if (this.themeConfig.surface_color) root.style.setProperty('--surface', this.themeConfig.surface_color);
    },

    render() {
        const navBrand = document.getElementById('navBrand');
        if (navBrand && this.etab) navBrand.textContent = `🍽️ ${this.etab.nom}`;
    }
};

// Toast helper
function showToast(message, type = '') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + type;
    setTimeout(function() { toast.classList.add('hidden'); }, 3000);
}

// Navigation event handlers
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.nav-link[data-page]').forEach(function(link) {
        link.addEventListener('click', function() {
            var page = this.dataset.page;
            document.querySelectorAll('.nav-link').forEach(function(l) { l.classList.remove('active'); });
            this.classList.add('active');
            // Navigate to WordPress pages
            if (page === 'accueil') window.location.href = '/';
            else window.location.href = '/' + page;
        });
    });
});
```

## Données lues depuis Supabase — mapping

| Composant | Source Supabase | Champs utilisés |
|---|---|---|
| Hero | `theme_config` | `hero_title`, `hero_subtitle`, `hero_image_url` |
| Logo + nom | `etablissements` | `logo_url`, `nom` |
| Catégories | `categories` | `id`, `nom`, `icone` |
| Produits | `produits` + `categories` | `id`, `nom`, `description`, `prix`, `photo_url`, `categories.nom` |
| Pages À Propos | `pages_etablissement` | `titre`, `contenu_html`, `contenu_css`, `ordre` |
| FAQ | `faqs` | `question`, `reponse` |
| Contact | `etablissements` | `adresse`, `telephone`, `email`, `site_web`, `horaires` (JSONB) |
| Couleurs thème | `theme_config` | `primary_color`, `secondary_color`, etc. |
| Réseaux sociaux | `etablissements` + `theme_config` | `reseaux_sociaux`, `facebook_url`, `instagram_url` |
| Commandes | `commandes` + `lignes_commande` (INSERT) | `client`, `produits`, `total` |

## Règles

1. **ZÉRO hardcoding** — toutes les couleurs viennent des CSS variables `var(--primary)`, etc.
2. **Fibonacci** — tous les espacements utilisent les variables `--space-*` (Fibonacci × 4px)
3. **Mobile-first** — le CSS est responsive, breakpoint à 700px
4. **Pas de jQuery** — JavaScript vanilla uniquement
5. **Supabase JS SDK v2** — chargé depuis CDN, pas de dépendance PHP pour les données
6. **WordPress ne stocke AUCUNE donnée métier** — tout vient de Supabase
7. **Panier en localStorage** — persiste entre les pages, survit au rechargement
8. **QR Table** — détection automatique du paramètre `?table=X` dans l'URL

## Emplacement

```
wp-content/themes/artizboard/   (à déployer sur Hostinger)
```

Les sources sont aussi versionnées dans :
```
C:\projet\wp-content\           (dépôt local de développement)
```

## 5. Step by Step — Implementation

| Ordre | Action | Fichier | Resultat |
|---|---|---|---|
| 1 | Créer style.css avec tokens M3 | `wp-content/themes/artizboard/` | CSS chargé |
| 2 | Créer PHP : header, footer, functions, index | `wp-content/themes/artizboard/` | Structure WP |
| 3 | Créer JS : config, api, cart, app | `wp-content/themes/artizboard/assets/js/` | Logique client |
| 4 | Injecter clés Supabase dans config.js | `deploy_site.py` | Connexion Supabase |
| 5 | Uploader via FTP sur Hostinger | `deploy_site.py` | Fichiers en ligne |
| 6 | Activer thème + créer pages WordPress | Admin WP | Site en ligne |
| 7 | Vérifier : cart, menu, à propos, contact | Navigateur | Toutes les sections OK |

## Checklist avant déploiement

- [ ] `SUPABASE_URL` et `SUPABASE_ANON_KEY` configurés dans `assets/js/config.js`
- [ ] Supabase RLS activé sur `commandes` et `lignes_commande` pour permettre les INSERT anonymes
- [ ] `etablissement_id` correct dans `getEtablissementId()`
- [ ] Images uploadées dans Supabase Storage (bucket `images` public)
- [ ] Champs `horaires` en JSONB valide dans `etablissements`
- [ ] `pages_etablissement` avec `contenu_html` + `contenu_css` remplis
- [ ] `theme_config` avec les couleurs, fonts et textes personnalisés
- [ ] WordPress installé sur Hostinger, thème activé
- [ ] Pages WordPress créées avec les templates correspondants :
  - Page "Carte" → Template: Carte / Menu
  - Page "À Propos" → Template: À Propos
  - Page "Contact" → Template: Contact
- [ ] Certificat SSL activé sur Hostinger
- [ ] Testé sur mobile (iPhone + Android)

## Déploiement automatique

```bash
python deploy_site.py
```

### Étapes

1. **Injecte** les clés Supabase depuis `config.ini` → `wp-content/themes/artizboard/assets/js/config.js`
2. **Upload** les fichiers du thème via FTP vers Hostinger
3. **Active** le thème via WordPress Admin (manuel car REST API souvent bloquée)
4. **Crée** les pages WordPress : `/carte`, `/apropos`, `/contact`

### Configuration Hostinger (config.ini)

```ini
[hostinger]
ftp_host = 77.37.37.209
ftp_port = 21
ftp_user = uXXXXXXXXX.aristodetoonasi.com
ftp_password = xxxxxx
wordpress_url = https://aristodetoonasi.com
wordpress_user = yaoplab@gmail.com
wordpress_app_password = xxxxxx
```

### Format des clés Supabase

Ancien format (JWT) : `eyJhbGciOiJIUzI1NiIs...`
**Nouveau format** (publishable/secret) : `sb_publishable_...` / `sb_secret_...`

Si tu changes/régénères les clés dans Supabase Dashboard → Settings → API :
1. Mets à jour `config.ini` avec les nouvelles clés
2. Relance `python deploy_site.py` (ça réinjecte les clés + réupload)

### Déploiement manuel

Si le FTP est bloqué :
1. `deploy_site.py` crée le ZIP dans `build/theme_upload/artizboard.zip`
2. Upload manuel via hPanel Hostinger → File Manager → `public_html/wp-content/themes/`
3. Extraire le ZIP → dossier `artizboard`
4. Mise à jour clés : éditer `config.js` directement dans le File Manager

### Page d'accueil WordPress vide

Le template `index.php` affiche le contenu WordPress ET le JavaScript remplit depuis Supabase.
Supprimer l'article "Hello World" dans WordPress Admin → Articles → Corbeille.

### Templates non visibles dans WordPress

Si les templates n'apparaissent pas dans le sélecteur "Modèle" :
1. Vérifier que le thème ArtizBoard est **actif** (Apparence → Thèmes)
2. Utiliser `page.php` (universel) qui détecte le slug et rend le bon contenu
3. Créer les pages sans se soucier du modèle — le JS s'adapte

### API REST bloquée (404)

Causes possibles et solutions :
1. **Permaliens** : Réglages → Permaliens → "Titre de la publication" → Enregistrer
2. **LiteSpeed Cache** : Désactiver le cache (Enable Cache → OFF) ou exclure `/wp-json`
3. **.htaccess absent** : Vérifier que le fichier contient les règles WordPress
4. **index.php manquant** à la racine `public_html/` : doit contenir `require __DIR__ . '/wp-blog-header.php';`
5. **Classic Editor** : Si Gutenberg ne fonctionne pas, installer le plugin Classic Editor

### Mise à jour des données

Les données (menu, pages, contact) viennent de Supabase en temps réel. Pour mettre à jour :
1. Modifier dans l'Admin ArtizBoard (`python -m apps.admin`)
2. Lancer la synchro : `python sync_service.py`
3. Rafraîchir le site — les nouvelles données apparaissent immédiatement
- [ ] Menu WordPress configuré pour pointer vers ces pages
- [ ] Certificat SSL activé sur Hostinger
- [ ] Testé sur mobile (iPhone + Android)
