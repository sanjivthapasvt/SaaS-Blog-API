import asyncio
import getpass
import re
import typer

from sqlmodel import select
from rich import print
from rich.console import Console
from pydantic import EmailStr, TypeAdapter

from dotenv import load_dotenv
load_dotenv()

from app.core.services.database import get_session, init_db as init_database
from app.auth.hashing import hash_password
from app.auth.security import check_password_strength
from app.users.models import User


err_console = Console(stderr=True)
app = typer.Typer()


@app.command()
def info():
    print("This is app for managing users, database and stuff")


@app.command()
def init_db():
    asyncio.run(init_database())
    print("[green]Database initialized.[/green]")


@app.command()
def createsuperuser():
    asyncio.run(_createsuperuser())


async def _createsuperuser():
    username: str = input("Enter username: ")
    full_name: str = input("Enter full name: ")
    email: EmailStr  = input("Enter email: ")
    password = getpass.getpass("Enter password: ")
    
    async for session in  get_session():
        try:
            username = re.sub(r"\s+", "", username)
            if username == "":
                err_console.print("[bold red]Username cannot be empty![/bold red]")
                return
            
            if full_name == "":
                err_console.print("[bold red]Full name cannot be empty![/bold red]")
                return
            
            # Check if username exists
            user = await session.execute(
                select(User).where(User.username == username)
            )
            if user.scalars().first():
                err_console.print("[bold red]User already exist[/bold red]")
                return
            try:
                TypeAdapter(EmailStr).validate_python(email)
            except Exception:
                err_console.print("[bold red]Enter a valid email![/bold red]")
                return
            
            # Check if email exists
            email_exist = await session.execute(select(User).where(User.email == email))
            if email_exist.scalars().first():
                err_console.print("[bold red]Email already exist[/bold red]")
                return

            
            strong, reasons = check_password_strength(password)
            if not strong:
                err_console.print(f"[bold red]Password is not strong! [/bold red]")
                user_input = input("Do you still want to continue?(Y/n)")
                if user_input.lower() != "y":
                    err_console.print(f"[bold red]{reasons}[/bold red]")
                    return
                
            hashed_password = hash_password(password)
            
            new_user = User(username=username,full_name=full_name, email=email, hashed_password=hashed_password, is_superuser=True)

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            print(f"[bold green]Superuser '{username}' created successfully![/bold green]")
            
        except Exception as e:
            err_console.print(f"[bold red]Something went wrong {e}[/bold red]")


if __name__ == "__main__":
    app()

