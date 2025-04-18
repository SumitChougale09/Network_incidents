from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager

# Create base class for SQL Alchemy models
class Base(DeclarativeBase):
    pass

# Create extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()