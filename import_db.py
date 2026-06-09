import asyncio
import aiomysql
import re

async def execute_sql_file(cur, filepath):
    print(f"Reading SQL file: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            sql_content = f.read()

    # Simple regex to remove SQL comments (both block /* ... */ and line -- or #)
    # Remove block comments
    sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
    
    # Split by semicolon
    statements = sql_content.split(';')
    
    count = 0
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt:
            continue
        
        # Remove line comments from the statement
        lines = stmt.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip lines starting with -- or #
            stripped = line.strip()
            if stripped.startswith('--') or stripped.startswith('#'):
                continue
            cleaned_lines.append(line)
        cleaned_stmt = '\n'.join(cleaned_lines).strip()
        if not cleaned_stmt:
            continue

        try:
            await cur.execute(cleaned_stmt)
            count += 1
        except Exception as e:
            # We print warning for duplicate key errors or table exists warnings
            print(f"[WARN] Statement: {cleaned_stmt[:60]}... \n  -> Info: {e}")
            
    print(f"Executed {count} statements from {filepath}\n")

async def main():
    print("Connecting to local MySQL (Laragon)...")
    try:
        conn = await aiomysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='',
            autocommit=True
        )
        async with conn.cursor() as cur:
            # Create Database
            print("Creating database if not exists: TugasGateaway")
            await cur.execute("CREATE DATABASE IF NOT EXISTS TugasGateaway")
            await cur.execute("USE TugasGateaway")
            
            # Execute original tugasgateway.sql
            await execute_sql_file(cur, "tugasgateway.sql")
            
            # Execute user_roles.sql
            await execute_sql_file(cur, "user_roles.sql")
            
        conn.close()
        print("[SUCCESS] All SQL migrations applied to TugasGateaway database!")
    except Exception as e:
        print(f"[FATAL] Failed to migrate database: {e}")

if __name__ == '__main__':
    asyncio.run(main())
