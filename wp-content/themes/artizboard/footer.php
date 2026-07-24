</main>

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

<div class="toast hidden" id="toast"></div>

<footer class="footer" id="footerContent">
    <p>© <?php echo date('Y'); ?> <?php bloginfo('name'); ?> — Propulsé par ArtizBoard</p>
    <p style="font-size:0.7rem;margin-top:4px;"><a href="<?php echo esc_url(home_url('/licence')); ?>" style="color:inherit;">Licence MIT</a></p>
</footer>

<script>
(function(){
    var path = window.location.pathname.replace(/\/$/, '');
    var page = 'accueil';
    if (/\/carte/.test(path)) page = 'carte';
    else if (/\/apropos/.test(path)) page = 'apropos';
    else if (/\/contact/.test(path)) page = 'contact';

    document.querySelectorAll('.nav-link').forEach(function(l){
        l.classList.toggle('active', l.dataset.page === page);
    });

    document.addEventListener('DOMContentLoaded', function(){
        if (typeof ArtizBoard !== 'undefined' && ArtizBoard.init) {
            ArtizBoard.init(page);
        }
    });
})();
</script>

<?php wp_footer(); ?>
</body>
</html>
