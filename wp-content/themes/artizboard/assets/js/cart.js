// Cart Management — localStorage

var CART_KEY = 'artizboard_cart';

function getCart() {
    try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; }
    catch(e) { return []; }
}
function saveCart(cart) { localStorage.setItem(CART_KEY, JSON.stringify(cart)); updateCartUI(); }
function clearCart() { localStorage.removeItem(CART_KEY); updateCartUI(); }
function getCartTotal() { return getCart().reduce(function(s,c){ return s + c.prix * c.qte; }, 0); }
function getCartCount() { return getCart().reduce(function(s,c){ return s + c.qte; }, 0); }
function getProdQty(pid) { var item = getCart().find(function(c){ return c.id === pid; }); return item ? item.qte : 0; }

function addToCart(produit) {
    var cart = getCart();
    var existing = cart.find(function(c){ return c.id === produit.id; });
    if (existing) existing.qte += 1;
    else cart.push({ id: produit.id, nom: produit.nom, prix: parseFloat(produit.prix), qte: 1 });
    saveCart(cart);
}

function removeFromCart(produitId) {
    var cart = getCart();
    var item = cart.find(function(c){ return c.id === produitId; });
    if (item) {
        item.qte -= 1;
        if (item.qte <= 0) cart = cart.filter(function(c){ return c.id !== produitId; });
    }
    saveCart(cart);
}

function updateCartUI() {
    var count = getCartCount();
    var badge = document.getElementById('cartBadge');
    var checkoutBtn = document.getElementById('checkoutBtn');
    if (badge) {
        if (count > 0) { badge.textContent = count; badge.classList.remove('hidden'); }
        else badge.classList.add('hidden');
    }
    if (checkoutBtn) checkoutBtn.disabled = count === 0;
    renderCartDrawer();
    if (typeof ArtizBoard !== 'undefined' && ArtizBoard.renderSearch) ArtizBoard.renderSearch();
}

function renderCartDrawer() {
    var itemsEl = document.getElementById('cartItems');
    var totalEl = document.getElementById('cartTotal');
    if (!itemsEl || !totalEl) return;

    var cart = getCart();
    itemsEl.innerHTML = '';
    if (cart.length === 0) {
        itemsEl.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🛒</div><p>Votre panier est vide</p></div>';
        totalEl.textContent = '0 FCFA';
        return;
    }

    cart.forEach(function(item){
        var div = document.createElement('div');
        div.className = 'cart-item';
        div.innerHTML = '<div><div style="font-weight:600">' + item.qte + 'x ' + item.nom + '</div><div style="font-size:0.75rem;color:var(--text-soft)">' + (item.prix*item.qte).toLocaleString() + ' FCFA</div></div><button class="cart-item-remove" data-id="' + item.id + '">✕</button>';
        itemsEl.appendChild(div);
    });
    totalEl.textContent = getCartTotal().toLocaleString() + ' FCFA';

    itemsEl.querySelectorAll('.cart-item-remove').forEach(function(btn){
        btn.addEventListener('click', function(){ removeFromCart(this.dataset.id); });
    });
}

async function checkout() {
    var cart = getCart();
    if (cart.length === 0) return;
    var eid = await getEtablissementId();
    var total = getCartTotal();
    var tableParam = new URLSearchParams(window.location.search).get('table');
    var ref = tableParam || 'Web';
    var cmdId = uuidv4();
    var commande = {
        id: cmdId, etablissement_id: eid, reference_client: ref,
        type_service: 'sur_place', statut: 'en_attente',
        statut_paiement: 'en_attente', total: total,
        created_at: new Date().toISOString()
    };
    var lignes = cart.map(function(c){
        return { id: uuidv4(), commande_id: cmdId, produit_id: c.id, quantite: c.qte, prix_unitaire: c.prix };
    });
    try {
        await submitCommande(commande, lignes);
        clearCart();
        showToast('Commande enregistree !', 'success');
    } catch(err) {
        showToast('Erreur : ' + (err.message || err), 'error');
    }
}

document.addEventListener('DOMContentLoaded', function(){
    var cartBtn = document.getElementById('cartBtn');
    var cartClose = document.getElementById('cartClose');
    var cartOverlay = document.getElementById('cartOverlay');
    var cartDrawer = document.getElementById('cartDrawer');
    var checkoutBtn = document.getElementById('checkoutBtn');

    function openCart(){ cartOverlay.classList.remove('hidden'); cartDrawer.classList.remove('hidden'); renderCartDrawer(); }
    function closeCart(){ cartOverlay.classList.add('hidden'); cartDrawer.classList.add('hidden'); }

    if(cartBtn) cartBtn.addEventListener('click', openCart);
    if(cartClose) cartClose.addEventListener('click', closeCart);
    if(cartOverlay) cartOverlay.addEventListener('click', closeCart);
    if(checkoutBtn) checkoutBtn.addEventListener('click', function(){ checkout().then(closeCart); });

    updateCartUI();
});
