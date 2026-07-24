<?php
/** Universal page — ArtizBoard */
get_header();
$slug = get_post_field('post_name', get_post());
?>
<div class="container">
    <div class="section-title"><?php the_title(); ?></div>
    <div id="<?php echo $slug === 'carte' ? 'carteContent' : ($slug === 'apropos' ? 'aproposContent' : 'contactContent'); ?>">
        <div class="loading">Chargement...</div>
    </div>
</div>
<script>
(function(){
    var s = '<?php echo $slug; ?>';
    var t = s === 'carte' ? 'carte' : (s === 'apropos' ? 'apropos' : 'contact');
    if (typeof ArtizBoard !== 'undefined') ArtizBoard.init(t);
})();
</script>
<?php get_footer(); ?>
