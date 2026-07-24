# WordPress Agent Reviewer

You review the WordPress theme deployment for ArtizBoard.

## Checklist

- [ ] `config.js` has valid `SUPABASE_URL` and `SUPABASE_ANON_KEY` (format `sb_publishable_...`)
- [ ] `style.css` uses CSS variables from the M3 design system
- [ ] `header.php` contains the nav with correct links (Accueil, Carte, À Propos, Contact)
- [ ] `footer.php` initializes `ArtizBoard.init(page)` with correct page slug
- [ ] `page.php` is present and handles carte/apropos/contact slugs
- [ ] `template-*.php` files exist but `page.php` is the universal fallback
- [ ] `functions.php` enqueues Supabase JS SDK from CDN + all app scripts
- [ ] `api.js` fetches from correct Supabase tables
- [ ] `cart.js` uses localStorage with key `artizboard_cart`
- [ ] `app.js` handles tab switching and Supabase data rendering
- [ ] FTP credentials in `config.ini` are valid (test with `python deploy_site.py`)
- [ ] Site loads data from Supabase (not showing "Hello World")
- [ ] LiteSpeed Cache is disabled or `/wp-json` is excluded
- [ ] `index.php` at `public_html/` root contains `require __DIR__ . '/wp-blog-header.php'`
- [ ] 10 theme presets are available in Admin → Apparence
