"""Create multiple staff members and distribute commands among them."""
import sys,uuid,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import psycopg2,psycopg2.extras
from datetime import datetime,timedelta,timezone

c=psycopg2.connect(host="127.0.0.1",port=5432,dbname="artizboard_local",
                    user="artizboard",password="artizboard_pass",client_encoding="UTF8")
c.autocommit=True
cur=c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("SELECT id FROM etablissements LIMIT 1")
EID=str(cur.fetchone()["id"])
cur.execute("SELECT id FROM utilisateurs WHERE email='admin@larepublique.tg'")
AID=str(cur.fetchone()["id"])

# Get role IDs
cur.execute("SELECT id FROM roles WHERE nom='admin'")
admin_role=cur.fetchone()["id"]
cur.execute("SELECT id FROM roles WHERE nom='serveur'")
serveur_role=cur.fetchone()["id"]

# Create staff members
staffs=[AID]
for name,email in [("Kofi Akakpo","kofi@larepublique.tg"),
                    ("Ama Mensah","ama@larepublique.tg"),
                    ("Yao Koffi","yao@larepublique.tg"),
                    ("Abi Lawson","abi@larepublique.tg")]:
    cur.execute("SELECT id FROM utilisateurs WHERE email=%s AND deleted_at IS NULL",(email,))
    r=cur.fetchone()
    if r:
        staffs.append(str(r["id"]))
    else:
        sid=str(uuid.uuid4())
        cur.execute("""INSERT INTO utilisateurs (id,etablissement_id,nom,email,role_id,created_by,updated_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",(sid,EID,name,email,serveur_role,AID,AID))
        staffs.append(sid)

# Update existing commands to distribute among staff
cur.execute("SELECT id FROM commandes WHERE deleted_at IS NULL ORDER BY created_at")
cmd_ids=[str(r["id"]) for r in cur.fetchall()]

updated=0
for i,cid in enumerate(cmd_ids):
    sid=staffs[i%len(staffs)]
    cur.execute("UPDATE commandes SET staff_id=%s WHERE id=%s",(sid,cid))
    updated+=1

cur.execute("SELECT u.nom,count(*),sum(c.total) FROM commandes c JOIN utilisateurs u ON c.staff_id=u.id WHERE c.deleted_at IS NULL GROUP BY u.nom ORDER BY sum DESC")
print("Repartition:")
for r in cur.fetchall():print(f"  {r['nom']}: {r['count']} cmd, {r['sum'] or 0:,.0f} F")
cur.close();c.close()
print(f"OK: {updated} commandes reparties entre {len(staffs)} serveurs")
