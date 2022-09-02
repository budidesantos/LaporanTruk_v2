from enum import unique
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Laporan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tgl_brgkt = db.Column(db.DateTime())
    tgl_kmbl = db.Column(db.DateTime())
    nopol = db.Column(db.String(100))
    sopir = db.Column(db.String(100))
    tujuan = db.Column(db.String(500))
    km_awal = db.Column(db.Integer)
    km_isi = db.Column(db.Integer)
    solar_awal = db.Column(db.Float)
    e_toll = db.Column(db.Integer)
    tujuan = db.Column(db.String(500))
    keterangan = db.Column(db.String(500))
    satpam1 = db.Column(db.String(100))
    satpam2 = db.Column(db.String(100))
    img = db.relationship('ImageSet', backref='laporan', lazy=True, uselist=True)

class ImageSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(150), nullable=False)
    laporan_id = db.Column(db.Integer, db.ForeignKey('laporan.id'), nullable=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))