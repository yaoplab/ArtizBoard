<?php
/**
 * ArtizBoard Theme Functions
 */

function artizboard_enqueue() {
    wp_enqueue_style('artizboard-style', get_stylesheet_uri(), [], '1.0');
    wp_enqueue_style('artizboard-font', 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap', [], null);

    wp_enqueue_script('supabase-js', 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2', [], null, true);
    wp_enqueue_script('artizboard-config', get_template_directory_uri() . '/assets/js/config.js', [], '1.0', true);
    wp_enqueue_script('artizboard-api', get_template_directory_uri() . '/assets/js/api.js', ['supabase-js', 'artizboard-config'], '1.0', true);
    wp_enqueue_script('artizboard-cart', get_template_directory_uri() . '/assets/js/cart.js', ['artizboard-api'], '1.0', true);
    wp_enqueue_script('artizboard-app', get_template_directory_uri() . '/assets/js/app.js', ['artizboard-cart'], '1.0', true);

    wp_localize_script('artizboard-config', 'wpArtizboard', [
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'templateUrl' => get_template_directory_uri(),
        'homeUrl' => home_url('/'),
    ]);
}
add_action('wp_enqueue_scripts', 'artizboard_enqueue');

function artizboard_setup() {
    add_theme_support('post-thumbnails');
    add_theme_support('title-tag');
    add_theme_support('html5', ['search-form', 'comment-form', 'style', 'script']);
    register_nav_menus([
        'primary' => 'Navigation principale',
        'footer' => 'Footer',
    ]);
}
add_action('after_setup_theme', 'artizboard_setup');

// Escaping helpers (noms pour le site côté admin génèrent des pages dynamiques)
function artizboard_pages() {
    return [
        'carte'    => ['slug' => 'carte',    'title' => 'Carte',    'template' => 'template-carte.php'],
        'apropos'  => ['slug' => 'apropos',  'title' => 'À Propos', 'template' => 'template-apropos.php'],
        'contact'  => ['slug' => 'contact',  'title' => 'Contact',  'template' => 'template-contact.php'],
    ];
}

// Expose page slugs to JS
function artizboard_head() {
    ?>
    <script>
        var ARTIZBOARD_HOME = '<?php echo esc_js(home_url('/')); ?>';
        var ARTIZBOARD_TEMPLATE = '<?php echo esc_js(get_page_template_slug()); ?>';
    </script>
    <?php
}
add_action('wp_head', 'artizboard_head');
