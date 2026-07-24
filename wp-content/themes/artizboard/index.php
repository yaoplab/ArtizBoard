<?php
/** Page d'accueil WordPress */
get_header();
?>
<div class="container">
    <?php
    while (have_posts()):
        the_post();
    ?>
    <div class="hero text-center">
        <h1 class="hero-title"><?php the_title(); ?></h1>
        <div class="hero-subtitle"><?php echo esc_html(get_post_meta(get_the_ID(), '_hero_subtitle', true) ?: 'Bienvenue sur notre portail.'); ?></div>
        <a href="<?php echo esc_url(home_url('/carte')); ?>" class="btn btn-primary">Voir la carte</a>
    </div>
    <div class="section">
        <?php the_content(); ?>
    </div>
    <?php endwhile; ?>
</div>
<?php get_footer(); ?>
