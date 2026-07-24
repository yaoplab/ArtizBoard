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
        <a href="<?php echo esc_url(home_url('/')); ?>" class="nav-brand" id="navBrand">
            🍽️ <?php bloginfo('name'); ?>
        </a>
        <div class="nav-links" id="navLinks">
            <a href="<?php echo esc_url(home_url('/')); ?>" class="nav-link active" data-page="accueil">Accueil</a>
            <a href="<?php echo esc_url(home_url('/carte')); ?>" class="nav-link" data-page="carte">🍽️ Carte</a>
            <a href="<?php echo esc_url(home_url('/apropos')); ?>" class="nav-link" data-page="apropos">ℹ️ À Propos</a>
            <a href="<?php echo esc_url(home_url('/contact')); ?>" class="nav-link" data-page="contact">📞 Contact</a>
            <button class="nav-link nav-cart" id="cartBtn">
                🛒 <span class="cart-badge hidden" id="cartBadge">0</span>
            </button>
        </div>
    </div>
</nav>

<main class="page-content" id="mainContent">
