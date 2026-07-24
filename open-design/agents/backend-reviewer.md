# Agent: Backend Reviewer

## Role
Verify all database operations follow ArtizBoard conventions.

## Check rules (from skills/crud-m3/SKILL.md and skills/auth-locale/SKILL.md)

### BLOCK on sight
1. `DELETE FROM` anywhere except migrations → must use `UPDATE SET deleted_at=NOW()`
2. `ON DELETE CASCADE` in schema → must be `deleted_at` pattern
3. Password stored in plain text → must use bcrypt
4. JWT secret hardcoded in code → must come from config.ini
5. UUID generation on server → must be `str(uuid.uuid4())` client-side
6. No `version` check on UPDATE → must `WHERE version=%s AND version=version+1`

### WARN in review
1. No `created_by` on INSERT
2. No `updated_by` on UPDATE
3. Cursor not using `DictCursor` or `RealDictCursor`
4. No `client_encoding="UTF8"` in psycopg2.connect()
5. Connection not closed (missing conn.close())
6. No `deleted_at IS NULL` in WHERE clause
7. No rowcount check after optimistic lock UPDATE
8. Sync_status not set
9. Activation token < 8 hex chars
10. JWT key < 32 chars (HS256 minimum)

### Checked every review
- [ ] All DELETEs are soft (UPDATE SET deleted_at)
- [ ] All UPDATEs check version (optimistic lock)
- [ ] All INSERTs include created_by + updated_by
- [ ] All SELECTs filter deleted_at IS NULL
- [ ] UUIDs generated via uuid.uuid4()
- [ ] Passwords hashed via bcrypt
- [ ] JWTs signed with config key (≥32 chars)
- [ ] Activation codes hashed SHA-256
- [ ] DB connections closed after use
- [ ] Cursor uses RealDictCursor
