// Supabase Configuration
// ⚠️ Remplacer par les vraies valeurs du projet Supabase
var SUPABASE_URL = 'https://zrfzibembigapzbgobwq.supabase.co';
var SUPABASE_ANON_KEY = 'sb_publishable_87JLZU00lT-M4EoBShWVqQ_ZYWMKO5k';

var supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
var ETABLISSEMENT_ID = null;

async function getEtablissementId() {
    if (ETABLISSEMENT_ID) return ETABLISSEMENT_ID;
    try {
        var result = await supabase.from('etablissements').select('id').limit(1).single();
        if (result.data) ETABLISSEMENT_ID = result.data.id;
    } catch(e) {}
    return ETABLISSEMENT_ID;
}