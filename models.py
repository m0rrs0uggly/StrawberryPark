from datetime import datetime
import uuid

from sqlalchemy import true
from app import db , login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    registration_no = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' , 'lecturer' , 'admin'
    created_at = db.Column(db.DateTime , default = datetime.utcnow)

    #relationships

    taught_units = db.relationship('Unit', backref='lecturer', lazy=True , foreign_keys='Unit.lecturer_id')

    grades = db.relationship('Grade', backref='student', lazy=True , cascade="all, delete-orphan")

    submitted_claims = db.relationship('MissingMarkClaim', backref='student', lazy=True, foreign_keys='MissingMarkClaim.student_id', cascade="all, delete-orphan")


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# unit model
class Unit(db.Model):
    __tablename__= 'units'

    id= db.Column(db.Integer, primary_key =True)
    code= db.Column(db.String(20), unique=True, nullable=False)
    title= db.Column(db.String(100), nullable=False)
    credit_hours= db.Column(db.Integer, nullable=False, default=3)
    lecturer_id= db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    #relationships
    grades = db.relationship('Grade', backref='unit', lazy=True, cascade="all, delete-orphan")
    claims = db.relationship('MissingMarkClaim', backref='unit', lazy=True, cascade="all, delete-orphan")


#grade models

class Grade(db.Model):
    __tablename__='grades'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    cat_score = db.Column(db.Float, nullable=True)
    exam_score = db.Column(db.Float, nullable=True)
    is_published = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def total_score(self):
        if self.cat_score is not None and self.exam_score is not None:
            return round(self.cat_score + self.exam_score, 2)
        elif self.cat_score is not None:
            return round(self.cat_score, 2)
        elif self.exam_score is not None:
            return round(self.exam_score, 2)
        return None

    @property
    def letter_grade(self):
        if self.cat_score is None or self.exam_score is None:
            return "INCOMPLETE"
        total = self.total_score
        if total >=70:
            return 'A'
        elif total >=60:
            return 'B'
        elif total >=50:
            return 'C'
        elif total >=40:
            return 'D'
        else:
            return 'F'

# missing mark claim model

class MissingMarkClaim(db.Model):
    __tablename__ = 'missing_mark_claims'

    id = db.Column(db.Integer, primary_key=True)
    claim_no = db.Column(db.String(50), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    assessment_type = db.Column(db.String(20), nullable=False)  # CAT, exam
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='PENDING')
    resolution_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Lecturer who resolved the claim


    #foreign key relationship to trck solver

    resolved_by = db.relationship('User', foreign_keys=[resolved_by_id], backref='resolved_claims', lazy=True)


    @staticmethod
    def generate_claim_no():
        return f"CLM-{uuid.uuid4().hex[:6].upper()}"