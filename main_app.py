from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from database import get_db
from models import User, Product
from auth import verify_password
from email_utils import send_low_stock_email

import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "fallbacksecret"))

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def landing_page(
    request: Request,
    name: str = "",
    min_stock: str = "",
    max_stock: str = "",
    min_amount: str = "",
    max_amount: str = "",
    low_stock_only: str = "",
    db: Session = Depends(get_db)
):
    query = db.query(Product)

    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))

    if min_stock.strip():
        query = query.filter(Product.stock >= int(min_stock))

    if max_stock.strip():
        query = query.filter(Product.stock <= int(max_stock))

    if min_amount.strip():
        query = query.filter(Product.amount >= int(min_amount))

    if max_amount.strip():
        query = query.filter(Product.amount <= int(max_amount))

    products = query.all()

    if low_stock_only == "yes":
        products = [p for p in products if p.stock <= p.amount * 0.25]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "products": products,
        "error": "",
        "filters": {
            "name": name,
            "min_stock": min_stock,
            "max_stock": max_stock,
            "min_amount": min_amount,
            "max_amount": max_amount,
            "low_stock_only": low_stock_only
        }
    })


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if user and verify_password(password, user.password_hash) and user.role == "admin":
        request.session["is_admin"] = True
        request.session["username"] = user.username
        return RedirectResponse(url="/admin", status_code=303)

    products = db.query(Product).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "products": products,
        "error": "Invalid admin login.",
        "filters": {
            "name": "",
            "min_stock": "",
            "max_stock": "",
            "min_amount": "",
            "max_amount": "",
            "low_stock_only": ""
        }
    })


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/", status_code=303)

    products = db.query(Product).all()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "products": products,
        "admin_username": request.session.get("username", "admin")
    })


@app.post("/admin/add")
def add_product(
    request: Request,
    name: str = Form(...),
    stock: int = Form(...),
    amount: int = Form(...),
    db: Session = Depends(get_db)
):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/", status_code=303)

    product = Product(name=name, stock=stock, amount=amount)
    db.add(product)
    db.commit()

    if stock <= amount * 0.25:
        send_low_stock_email(name, stock, amount)

    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/update/{product_id}")
def update_product(
    request: Request,
    product_id: int,
    name: str = Form(...),
    stock: int = Form(...),
    amount: int = Form(...),
    db: Session = Depends(get_db)
):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/", status_code=303)

    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.name = name
        product.stock = stock
        product.amount = amount
        db.commit()

        if stock <= amount * 0.25:
            send_low_stock_email(name, stock, amount)

    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/delete/{product_id}")
def delete_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db)
):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/", status_code=303)

    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()

    return RedirectResponse(url="/admin", status_code=303)
