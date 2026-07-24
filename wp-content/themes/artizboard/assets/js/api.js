// API Wrapper for Supabase

function objOrNull(result) { return result.data ? result.data : null; }
function arrOrEmpty(result) { return result.data || []; }

async function fetchEtablissement(eid) {
    var result = await supabase.from('etablissements').select('*').limit(1).single();
    return objOrNull(result);
}

async function fetchCategories(eid) {
    var result = await supabase.from('categories').select('*').eq('etablissement_id', eid).order('nom');
    return arrOrEmpty(result);
}

async function fetchProduits(eid) {
    var result = await supabase.from('produits')
        .select('*, categories!inner(nom)')
        .eq('etablissement_id', eid)
        .eq('permets_commande', true)
        .order('nom');
    return arrOrEmpty(result);
}

async function fetchPages(eid) {
    var result = await supabase.from('pages_etablissement')
        .select('*')
        .eq('etablissement_id', eid)
        .eq('est_active', true)
        .order('ordre');
    return arrOrEmpty(result);
}

async function fetchFAQs(eid) {
    var result = await supabase.from('faqs')
        .select('*')
        .eq('etablissement_id', eid)
        .order('ordre');
    return arrOrEmpty(result);
}

async function fetchThemeConfig(eid) {
    try {
        var result = await supabase.from('theme_config')
            .select('*')
            .eq('etablissement_id', eid)
            .eq('est_actif', true)
            .limit(1)
            .single();
        return objOrNull(result);
    } catch(e) { return null; }
}

async function submitCommande(commande, lignes) {
    var cmdResult = await supabase.from('commandes').insert([commande]).select();
    if (cmdResult.error) throw cmdResult.error;
    if (!cmdResult.data || cmdResult.data.length === 0) throw new Error('Commande non creee');

    var cmdId = cmdResult.data[0].id;
    for (var i = 0; i < lignes.length; i++) {
        lignes[i].commande_id = cmdId;
    }
    var lineResult = await supabase.from('lignes_commande').insert(lignes);
    if (lineResult.error) throw lineResult.error;

    return cmdResult.data[0];
}

function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}
