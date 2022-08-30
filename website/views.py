from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, Response
from flask_login import login_required, current_user
from sqlalchemy import desc
from .models import Laporan, ImageSet
import xlwt
import io
import os
import secrets
from PIL import Image
from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, DateField, IntegerField, TextAreaField, DecimalField # , FieldList, FormField, HiddenField
from wtforms.validators import DataRequired
from . import db
import json

views = Blueprint('views', __name__)

# class FormImage(FlaskForm):
#     image =  FileField('Tambahkan Foto', validators=[FileAllowed(['jpg', 'png'])])

# Form untuk Laporan Berangkat(add & update)
class FormBerangkat(FlaskForm):
    nopol = StringField('Nomor Polisi', validators=[DataRequired()])
    sopir = StringField('Nama Sopir', validators=[DataRequired()])
    km_awal = IntegerField('KM Awal', validators=[DataRequired()])
    solar_awal = DecimalField('Solar Awal (L)', validators=[DataRequired()])
    e_toll = IntegerField('E-Toll')
    tujuan = TextAreaField('Tujuan')
    foto = FileField('Tambahkan Foto', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Submit')

# Form untuk Laporan Kembali(add & update)
class FormKembali(FlaskForm):
    nopol = StringField('Nomor Polisi', validators=[DataRequired()])
    sopir = StringField('Nama Sopir', validators=[DataRequired()])
    km_isi = IntegerField('KM Isi', validators=[DataRequired()])
    keterangan = TextAreaField('Keterangan')
    foto = FileField('Tambahkan Foto', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Submit')

class FormIndex(FlaskForm):
    index_ats = DateField('Dari Tanggal :', validators=[DataRequired()])
    index_bwh = DateField('Sampai Tanggal :', validators=[DataRequired()])
    submit = SubmitField('Confirm')

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    list_laporan = Laporan.query.order_by(desc(Laporan.tgl_brgkt)).paginate(page = page, per_page=30)
    # form_index = FormIndex()
    # if form_index.validate_on_submit():
    #     atas = form_index.index_ats.data()
    #     bawah = form_index.index_bwh.data()
    #     index_laporan = Laporan.query.filter(Laporan.tgl_brgkt<=atas, Laporan.tgl_brgkt >=bawah).order_by(desc(Laporan.tgl_brgkt)).paginate(page = page, per_page=30)
        
    #     return render_template("home.html", form = form_index, user=current_user, laporan=index_laporan)
    return render_template("home.html", user=current_user, laporan=list_laporan)

#detail laporan
@views.route('/laporan/<int:id>')
def laporan(id):
    laporan =  Laporan.query.get_or_404(id)
    foto = []
    if ImageSet.query.filter(ImageSet.laporan_id==id):
        for list in ImageSet.query.filter(ImageSet.laporan_id==id):
            foto.append(url_for('static', filename='images/laporan_images/' + list.image))
            print(foto)
    return render_template('laporan.html', user=current_user, laporan=laporan, img=foto)


# upload img
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(views.root_path, 'static/images/laporan_images', picture_fn)
    output_size = (480, 270)
    
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

#tambah laporan berangkat
@views.route('/add-berangkat', methods=['GET', 'POST'])
@login_required
def add_berangkat():
    form = FormBerangkat()
    if form.validate_on_submit():
        nopol = form.nopol.data.upper()
        sopir = form.sopir.data.upper()
        km_awal = form.km_awal.data
        solar_awal = form.solar_awal.data
        e_toll = form.e_toll.data
        tujuan = form.tujuan.data
        file_foto = form.foto.data
        print(file_foto)
        
        cek_nopol = Laporan.query.order_by(desc(Laporan.id)).filter_by(nopol=nopol).first()
            
        if cek_nopol:
            laporan = Laporan.query.get_or_404(cek_nopol.id)
            if laporan.tgl_kmbl==None:
                flash('Nomor polisi atau sopir sudah terdaftar di laporan berangkat dan belum kembali', category='error')          
            else:
                new_post = Laporan(tgl_brgkt=date.today(), nopol=nopol, sopir=sopir, km_awal=km_awal, km_isi=0, solar_awal=solar_awal, e_toll=e_toll, tujuan=tujuan)
                db.session.add(new_post)
                db.session.flush() #
                if file_foto:
                    foto = save_picture(file_foto)
                    new_foto = ImageSet(laporan_id=new_post.id, image= foto)
                    db.session.add(new_foto) #
                db.session.commit()
                return redirect(url_for('views.home'))
        else:
            new_post = Laporan(tgl_brgkt=date.today(), nopol=nopol, sopir=sopir, km_awal=km_awal, km_isi=0, solar_awal=solar_awal, e_toll=e_toll, tujuan=tujuan)
            db.session.add(new_post)
            db.session.flush() #
            if file_foto:
                foto = save_picture(file_foto)
                new_foto = ImageSet(laporan_id=new_post.id, image= foto)
                db.session.add(new_foto) #
            db.session.commit()
            return redirect(url_for('views.home'))
    return render_template("add_brgkt.html", title="Tambah Laporan Truk Berangkat", form = form, user=current_user)

@views.route('/add-kembali', methods=['GET', 'POST'])
@login_required
def add_kembali():
    form = FormKembali()
    if form.validate_on_submit():
        nopol = form.nopol.data.upper()
        sopir = form.sopir.data.upper()
        km_isi = form.km_isi.data
        keterangan = form.keterangan.data
        file_foto = form.foto.data

        cek_nopol = Laporan.query.order_by(desc(Laporan.id)).filter_by(nopol=nopol).first()
        cek_sopir = Laporan.query.order_by(desc(Laporan.id)).filter_by(sopir=sopir).first()
        if cek_nopol and cek_sopir:
            laporan = Laporan.query.get_or_404(cek_nopol.id)
            if laporan.tgl_kmbl==None:
                laporan.tgl_kmbl = date.today()
                laporan.km_isi = km_isi
                laporan.keterangan = keterangan
                if file_foto:
                    foto = save_picture(file_foto)
                    new_foto = ImageSet(laporan_id=laporan.id, image= foto)
                    db.session.add(new_foto)
                db.session.commit()
                return redirect(url_for('views.home'))
            else:
                flash(f'Error! Truk {cek_nopol.nopol} telah kembali', category='error')
        else:
            flash('Error!', category='error')
    return render_template("add_kmbl.html", title="Tambah Laporan Truk Kembali", form = form, user=current_user)

#hapus laporan
@views.route('/laporan/<int:id>/delete', methods=['POST'])
@login_required
def delete_laporan(id):
    laporan = Laporan.query.get_or_404(id)
    if current_user.username!='admin':
        abort(403)
    if ImageSet.query.filter(ImageSet.laporan_id==id):
        for list in ImageSet.query.filter(ImageSet.laporan_id==id):
            os.remove(os.path.join(views.root_path, 'static/images/laporan_images', list.image))
        ImageSet.query.filter(ImageSet.laporan_id==id).delete()
    db.session.delete(laporan)
    db.session.commit()
    flash('Laporan berhasil dihapus', 'success')
    return redirect(url_for('views.home'))

# list nopol
@views.route('/nopol', methods=['GET'])
@login_required
def get_nopol_list():
    list_laporan = Laporan.query.order_by(desc(Laporan.nopol))
    list_nopol = []
    jum_list = []
    for list in list_laporan:
        if list.nopol in list_nopol:
            jum_list[list_nopol.index(list.nopol)] += 1
        else:
            list_nopol.append(list.nopol)
            jum_list.append(1)
    data = sorted(zip(jum_list, list_nopol), key = lambda x: (-x[0], x[1]))
    return render_template('list_nopol.html', title="List Nomor Polisi",  data=data, user=current_user)

#list sopir
@views.route('/sopir', methods=['GET'])
@login_required
def get_sopir_list():
    list_laporan = Laporan.query.order_by(desc(Laporan.sopir))
    list_sopir = []
    jum_list = []
    for list in list_laporan:
        if list.sopir in list_sopir:
            jum_list[list_sopir.index(list.sopir)] += 1
        else:
            list_sopir.append(list.sopir)
            jum_list.append(1)
    data = sorted(zip(jum_list, list_sopir), key = lambda x: (-x[0], x[1]))
    return render_template('list_sopir.html', title="List Sopir",  data=data, user=current_user)



#list laporan berdasarkan nopol
@views.route('/nopol/<nopol>', methods=['GET'])
@login_required
def laporan_nopol(nopol):
    page = request.args.get('page', 1, type=int)
    list_laporan = Laporan.query.filter(Laporan.nopol==nopol).order_by(desc(Laporan.tgl_brgkt)).paginate(page = page, per_page=20)
    return render_template("home.html", user=current_user, laporan=list_laporan)

#list laporan berdasarkan sopir
@views.route('/sopir/<sopir>', methods=['GET'])
@login_required
def laporan_sopir(sopir):
    page = request.args.get('page', 1, type=int)
    list_laporan = Laporan.query.filter(Laporan.sopir==sopir).order_by(desc(Laporan.tgl_brgkt)).paginate(page = page, per_page=20)
    return render_template("home.html", user=current_user, laporan=list_laporan)

# # download Laporan to excel
# @views.route('/download/laporan/', methods=['GET'])
# def download_laporan():
#     try:
#         data = Laporan.session.query.all()
#         output = io.BytesIO()

#         workbook = xlwt.Workbook()

#         dl = workbook.add_sheet('Laporan Truk')

#         dl.write(0, 1, 'Tanggal Laporan')
#         dl.write(0, 2, 'Nomor Polisi')
#         dl.write(0, 3, 'Nama Sopir')
#         dl.write(0, 4, 'KM Awal')
#         dl.write(0, 5, 'KM Isi')
#         dl.write(0, 6, 'Isi Solar Awal')
#         dl.write(0, 7, 'Tujuan')
#         dl.write(0, 8, 'E-Toll')
    
#         idx = 0
#         for row in data:
#             dl.write(idx+1, 1, str(row.tanggal))
#             dl.write(idx+1, 2, row.nopol)
#             dl.write(idx+1, 3, row.sopir)
#             dl.write(idx+1, 4, row.km_awal)
#             dl.write(idx+1, 5, row.km_isi)
#             dl.write(idx+1, 6, row.solar_awal)
#             dl.write(idx+1, 7, row.keterangan)
#             dl.write(idx+1, 8, row.e_toll)
#             idx += 1

#         workbook.save(output)
#         output.seek(0)
 
#         return Response(output, mimetype="application/ms-excel", headers={"Content-Disposition":"attachment;filename=download.xls"})
#     except Exception as e:
# 	    print(e)

