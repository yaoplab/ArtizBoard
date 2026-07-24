// ArtizBoard — Main App

var ArtizBoard = {
    etab: null, categories: [], produits: [], pages: [], faqs: [], themeConfig: null,
    activeTab: 0, activeCat: null, activePage: 0,

    async init(page) {
        this.activeTab = ['accueil','carte','apropos','contact'].indexOf(page);
        await this.loadData();
        this.applyTheme();
        this.updateBrand();
        this.render();
    },

    async loadData() {
        try {
            var eid = await getEtablissementId();
            var results = await Promise.all([
                fetchEtablissement(eid), fetchCategories(eid), fetchProduits(eid),
                fetchPages(eid), fetchFAQs(eid), fetchThemeConfig(eid)
            ]);
            this.etab = results[0];
            this.categories = results[1];
            this.produits = results[2];
            this.pages = results[3];
            this.faqs = results[4];
            this.themeConfig = results[5];
            // URL param override for testing: ?theme=resto-luxe
            var urlTheme = new URLSearchParams(window.location.search).get('theme');
            if (urlTheme && this.themeConfig) {
                this.themeConfig.theme_id = urlTheme;
                // Load preset for this theme
                var preset = this.themeConfig;
                if (!preset.theme_id) preset.theme_id = urlTheme;
            }
        } catch(e) { console.error('Load error:', e); }
    },

    applyTheme() {
        if (!this.themeConfig) return;
        var root = document.documentElement.style;
        var tc = this.themeConfig;
        if (tc.primary_color) root.setProperty('--primary', tc.primary_color);
        if (tc.primary_dark) root.setProperty('--primary-dark', tc.primary_dark);
        if (tc.secondary_color) root.setProperty('--secondary', tc.secondary_color);
        if (tc.accent_color) root.setProperty('--accent', tc.accent_color);
        if (tc.surface_color) root.setProperty('--surface', tc.surface_color);
        if (tc.font_heading) document.body.style.setProperty('--font', tc.font_heading + ', sans-serif');
        if (tc.custom_css) {
            var styleEl = document.getElementById('artizboard-custom-css');
            if (!styleEl) {
                styleEl = document.createElement('style');
                styleEl.id = 'artizboard-custom-css';
                document.head.appendChild(styleEl);
            }
            styleEl.textContent = tc.custom_css;
        }
    },

    updateBrand() {
        var brand = document.getElementById('navBrand');
        if (brand && this.etab) {
            var logo = this.etab.logo_url ? '<img src="' + this.etab.logo_url + '" alt="Logo">' : '';
            brand.innerHTML = logo + ' ' + (this.etab.nom || '');
        }
    },

    render() {
        var el;
        if (this.activeTab === 0) this.renderAccueil();
        else if (this.activeTab === 1) this.renderCarte();
        else if (this.activeTab === 2) this.renderApropos();
        else if (this.activeTab === 3) this.renderContact();
    },

    // ── ACCUEIL ──
    renderAccueil() {
        var content = document.getElementById('mainContent');
        if (!content) return;
        var tc = this.themeConfig || {};
        var etab = this.etab || {};

        var heroTitle = tc.hero_title || etab.nom || 'Notre Etablissement';
        var heroSub = tc.hero_subtitle || etab.mission || 'Bienvenue sur notre portail.';

        var catsHTML = '';
        if (this.categories.length > 0) {
            catsHTML = '<div class="section"><div class="container"><h2 class="section-title">Nos categories</h2><div style="display:flex;flex-wrap:wrap;gap:var(--space-sm)">';
            this.categories.slice(0,6).forEach(function(c){
                catsHTML += '<a href="' + ARTIZBOARD_HOME + 'carte" class="btn btn-outline">' + (c.icone||'') + ' ' + c.nom + '</a>';
            });
            catsHTML += '</div></div></div>';
        }

        content.innerHTML =
            '<div class="hero"><div class="container"><h1 class="hero-title">' + heroTitle + '</h1>' +
            '<div class="hero-subtitle">' + heroSub + '</div>' +
            '<a href="' + ARTIZBOARD_HOME + 'carte" class="btn btn-primary">' + (tc.hero_button_text || 'Voir la carte') + '</a></div></div>' +
            catsHTML +
            '<div class="section"><div class="container"><div class="text-center" style="margin:var(--space-xl)0"><h2 class="section-title">Notre Engagement</h2><p style="color:var(--text-soft);max-width:600px;margin:0 auto">' + (etab.mission || 'Offrir une experience culinaire exceptionnelle.') + '</p></div></div></div>';
    },

    // ── CARTE ──
    renderCarte() {
        var self = this;
        var el = document.getElementById('carteContent') || document.getElementById('mainContent');
        if (!el) return;

        // Bistro mode: sidebar + products side-by-side
        if (this.themeConfig && this.themeConfig.theme_id === 'resto-bistro') {
            this.renderCarteBistro(el);
            return;
        }

        if (this.activeCat) {
            var cat = this.categories.find(function(c){ return c.id === ArtizBoard.activeCat; });
            var prods = this.produits.filter(function(p){ return p.categorie_id === ArtizBoard.activeCat; });
            var backBtn = '<button class="btn btn-outline" style="margin-bottom:var(--space-md)" onclick="ArtizBoard.activeCat=null;ArtizBoard.renderCarte();">← Retour</button>';
            var title = '<h2 class="section-title">' + (cat ? cat.nom : '') + '</h2>';
            var grid = '<div class="product-grid" style="margin-top:var(--space-md)">' + prods.map(function(p){
                var qty = getProdQty(p.id);
                return '<div class="product-card' + (qty>0?' in-cart':'') + '">' +
                    (p.photo_url ? '<img class="product-image" src="' + p.photo_url + '" alt="' + p.nom + '" loading="lazy">' : '<div class="product-image" style="display:flex;align-items:center;justify-content:center;font-size:1.5rem">🍽️</div>') +
                    '<div class="product-info"><div class="product-name">' + p.nom + '</div><div class="product-desc">' + (p.description||'') + '</div><div class="product-price">' + parseFloat(p.prix).toLocaleString() + ' FCFA</div></div>' +
                    '<div class="product-actions"><button class="qty-btn" onclick="event.stopPropagation();removeFromCart(\'' + p.id + '\');ArtizBoard.renderCarte();">−</button>' +
                    '<span class="qty-value">' + qty + '</span>' +
                    '<button class="qty-btn" onclick="event.stopPropagation();addToCart({id:\'' + p.id + '\',nom:\'' + p.nom.replace(/'/g,"\\'") + '\',prix:' + p.prix + '});ArtizBoard.renderCarte();">+</button></div></div>';
            }).join('') + '</div>';
            el.innerHTML = '<div class="container">' + backBtn + title + grid + '</div>';
        } else {
            var list = '<div class="cat-list">' + this.categories.map(function(c){
                var count = ArtizBoard.produits.filter(function(p){ return p.categorie_id === c.id; }).length;
                return '<div class="cat-item" onclick="ArtizBoard.activeCat=\'' + c.id + '\';ArtizBoard.renderCarte();">' +
                    '<span class="cat-item-name">' + (c.icone||'') + ' ' + c.nom + '</span>' +
                    '<span class="cat-item-count">' + count + ' plats</span></div>';
            }).join('') + '</div>';
            // Search
            var searchHTML = '<div style="margin-bottom:var(--space-md)"><input type="text" id="prodSearch" class="qty-btn" style="width:100%;padding:12px;border-radius:var(--shape-full);border:1px solid var(--outline-variant);font-family:var(--font)" placeholder="Rechercher un plat..."></div>';
            el.innerHTML = '<div class="container">' + searchHTML + list + '</div>';

            document.getElementById('prodSearch').addEventListener('input', function(){
                var q = this.value.toLowerCase();
                document.querySelectorAll('.cat-item').forEach(function(item){
                    item.style.display = item.querySelector('.cat-item-name').textContent.toLowerCase().indexOf(q) >= 0 ? 'flex' : 'none';
                });
            });
        }
    },

    // ── CARTE BISTRO ──
    renderCarteBistro(el) {
        var self = this;

        var sidebarHTML = '<div class="bistro-sidebar"><div class="bistro-sidebar-header">Catégories</div><div class="cat-list">' +
            this.categories.map(function(c){
                var count = self.produits.filter(function(p){ return p.categorie_id === c.id; }).length;
                var activeClass = (self.activeCat === c.id) ? ' cat-item-active' : '';
                return '<div class="cat-item' + activeClass + '" onclick="ArtizBoard.activeCat=\'' + c.id + '\';ArtizBoard.renderCarte();">' +
                    '<span class="cat-item-name">' + (c.icone||'') + ' ' + c.nom + '</span>' +
                    '<span class="cat-item-count">' + count + '</span></div>';
            }).join('') +
        '</div></div>';

        var cat = self.activeCat ? self.categories.find(function(c){ return c.id === self.activeCat; }) : null;
        var prods = self.activeCat
            ? self.produits.filter(function(p){ return p.categorie_id === self.activeCat; })
            : self.produits;

        var titleHTML = cat
            ? '<h2 class="section-title">' + cat.nom + '</h2>'
            : '<h2 class="section-title">Tous les produits</h2>';

        var productsHTML = '<div class="product-grid">' + prods.map(function(p){
            var qty = getProdQty(p.id);
            return '<div class="product-card' + (qty>0?' in-cart':'') + '">' +
                (p.photo_url ? '<img class="product-image" src="' + p.photo_url + '" alt="' + p.nom + '" loading="lazy">' : '<div class="product-image" style="display:flex;align-items:center;justify-content:center;font-size:1.5rem">🍽️</div>') +
                '<div class="product-info"><div class="product-name">' + p.nom + '</div><div class="product-desc">' + (p.description||'') + '</div><div class="product-price">' + parseFloat(p.prix).toLocaleString() + ' FCFA</div></div>' +
                '<div class="product-actions"><button class="qty-btn" onclick="event.stopPropagation();removeFromCart(\'' + p.id + '\');ArtizBoard.renderCarte();">−</button>' +
                '<span class="qty-value">' + qty + '</span>' +
                '<button class="qty-btn" onclick="event.stopPropagation();addToCart({id:\'' + p.id + '\',nom:\'' + p.nom.replace(/'/g,"\\'") + '\',prix:' + p.prix + '});ArtizBoard.renderCarte();">+</button></div></div>';
        }).join('') + '</div>';

        var mainHTML = '<div class="bistro-main">' + titleHTML + productsHTML + '</div>';

        el.innerHTML = '<div class="bistro-layout">' + sidebarHTML + mainHTML + '</div>';
    },

    // ── À PROPOS ──
    renderApropos() {
        var el = document.getElementById('aproposContent') || document.getElementById('mainContent');
        if (!el) return;
        var html = '<div class="container">';

        // Pages sub-nav
        if (this.pages.length > 1) {
            html += '<div class="page-subnav">';
            this.pages.forEach(function(p, i){
                html += '<button class="page-tab' + (i===ArtizBoard.activePage?' active':'') + '" onclick="ArtizBoard.activePage=' + i + ';ArtizBoard.renderApropos();">' + p.titre + '</button>';
            });
            html += '</div>';
        }

        // Current page content
        if (this.pages.length > 0) {
            var p = this.pages[this.activePage];
            html += '<h2 class="section-title">' + p.titre + '</h2>';
            html += '<div class="html-content">' + (p.contenu_html || '') + '</div>';
        } else {
            var etab = this.etab || {};
            html += '<h2 class="section-title">A Propos</h2>';
            html += '<div class="html-content"><p>' + (etab.historique || '') + '</p><h3>Notre Mission</h3><p>' + (etab.mission || '') + '</p></div>';
        }

        // FAQ
        if (this.faqs.length > 0) {
            html += '<div class="section"><h2 class="section-title">Questions frequentes</h2>';
            this.faqs.forEach(function(f){
                html += '<div class="faq-item"><div class="faq-question">' + f.question + '</div><div class="faq-answer">' + f.reponse + '</div></div>';
            });
            html += '</div>';
        }

        html += '</div>';
        el.innerHTML = html;
    },

    // ── CONTACT ──
    renderContact() {
        var el = document.getElementById('contactContent') || document.getElementById('mainContent');
        if (!el) return;
        var e = this.etab || {};

        var horaires = {};
        try { horaires = typeof e.horaires === 'string' ? JSON.parse(e.horaires) : (e.horaires || {}); } catch(_){}
        var jours = ['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'];
        var joursKey = ['lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche'];

        var hoursHTML = '<table class="hours-table">';
        jours.forEach(function(j, i){
            var h = horaires[joursKey[i]] || '—';
            hoursHTML += '<tr><td>' + j + '</td><td>' + h + '</td></tr>';
        });
        hoursHTML += '</table>';

        var html = '<div class="container">' +
            '<div class="contact-grid">' +
            '<div class="contact-card"><div class="contact-icon">📍</div><h3>Adresse</h3><p>' + (e.adresse||'—') + '</p></div>' +
            '<div class="contact-card"><div class="contact-icon">📞</div><h3>Telephone</h3><p>' + (e.telephone||'—') + '</p></div>' +
            '<div class="contact-card"><div class="contact-icon">📧</div><h3>Email</h3><p>' + (e.email||'—') + '</p></div>' +
            '<div class="contact-card"><div class="contact-icon">🌐</div><h3>Site web</h3><p>' + (e.site_web||'—') + '</p></div>' +
            '</div>' +
            '<div class="section"><h2 class="section-title">Horaires d\'ouverture</h2>' + hoursHTML + '</div>' +
            '<div class="section"><h2 class="section-title">Moyens de paiement</h2><p style="color:var(--text-soft)">' + (e.moyens_paiement_acceptes||'Carte, Especes') + '</p></div>' +
            '</div>';

        el.innerHTML = html;
    }
};

// Toast
function showToast(message, type) {
    var toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + (type||'');
    setTimeout(function(){ toast.classList.add('hidden'); }, 3000);
}

// Highlight active nav
(function(){
    var path = window.location.pathname.replace(/\/$/, '');
    document.querySelectorAll('.nav-link').forEach(function(l){
        if (path === '/' && l.dataset.page === 'accueil') l.classList.add('active');
        else if (path.indexOf('/' + l.dataset.page) === 0) l.classList.add('active');
        else l.classList.remove('active');
    });
})();
