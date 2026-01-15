import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy import select
from config.database import get_async_session, async_engine
from models.user import User, UserAuth
from utils.security import SecurityManager


async def check():
    print("Connecting to database...")
    try:
        async for db in get_async_session():
            print("--- Users ---")
            result = await db.execute(select(User))
            users = result.scalars().all()
            if not users:
                print("No users found!")
            for u in users:
                print(f"User: id={u.id}, username='{u.username}', email='{u.email}'")
                if u.password_hash:
                    is_valid = SecurityManager.verify_password(
                        "123456", u.password_hash
                    )
                    print(f"  Password '123456' matches? {is_valid}")
                else:
                    print("  No password hash set")

            print("\n--- User Auths ---")
            result = await db.execute(select(UserAuth))
            auths = result.scalars().all()
            if not auths:
                print("No auth records found!")
            for a in auths:
                print(
                    f"Auth: user_id={a.user_id}, type='{a.auth_type}', key='{a.auth_key}', verified={a.is_verified}"
                )

            # Close session (loop runs once)
            await db.close()
            break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(check())
