from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

Base = declarative_base()

# User table


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

# Category table


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    # serialize function used to create JSON endpoint
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }

# Item table


class Item(Base):
    __tablename__ = 'item'

    title = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(4000))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    # set created date to the current system date
    created_date = Column(DateTime(timezone=True), server_default=func.now())

    # serialize function used to create JSON endpoint
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'title': self.title,
            'description': self.description,
            'id': self.id,
            'category': self.category_id,
        }


engine = create_engine('postgresql:///catalog')

# Check if the database already exists, if it doesn't create it
if not database_exists(engine.url):
    create_database(engine.url)
else:
    print "Database 'catelog' already exists."

# if __name__ == '__main__':
#     print(database_exists(engine.url))

Base.metadata.create_all(engine)
