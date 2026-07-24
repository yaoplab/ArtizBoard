"""Reset sync state to local for all tables."""
import psycopg2
c = psycopg2.connect(host='127.0.0.1', port=55515, dbname='ArtizBoard', user='postgres', password='postgres')
cur = c.cursor()
tables = ['etablissements','utilisateurs','categories','produits','faqs','pages_etablissement','theme_config']
for t in tables:
    cur.execute(f"UPDATE {t} SET sync_status='local', updated_at=NOW() WHERE deleted_at IS NULL")
    print(f"  {t}: {cur.rowcount} rows reset")
c.commit()
cur.close()
c.close()
print("Done — ready to sync")
