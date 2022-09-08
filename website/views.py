from urllib import response
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, Response
from flask_login import login_required, current_user
from sqlalchemy import desc
from .models import Laporan, ImageSet
import xlwt
import io
import os
import secrets
from PIL import Image
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, IntegerField, TextAreaField, DecimalField, DateField # , FieldList, FormField, HiddenField
from wtforms.validators import DataRequired
from . import db

views = Blueprint('views', __name__)

# Form untuk Laporan Berangkat(add & update)
class FormBerangkat(FlaskForm):
    nopol = StringField('Nomor Polisi', validators=[DataRequired()])
    sopir = StringField('Nama Sopir', validators=[DataRequired()])
    satpam1 = StringField('Nama Satpam', validators=[DataRequired()])
    km_awal = IntegerField('KM Berangkat', validators=[DataRequired()])
    tujuan = TextAreaField('Tujuan')
    foto = FileField('Tambahkan Foto', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('Submit')

# Form untuk Laporan Kembali(add & update)
class FormKembali(FlaskForm):
    nopol = StringField('Nomor Polisi', validators=[DataRequired()])
    sopir = StringField('Nama Sopir', validators=[DataRequired()])
    satpam2 = StringField('Nama Satpam', validators=[DataRequired()])
    km_isi = IntegerField('KM Kembali', validators=[DataRequired()])
    keterangan = TextAreaField('Keterangan')
    foto = FileField('Tambahkan Foto', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Submit')

# Form edit
class LaporanAdmin(FlaskForm):
    nopol = StringField('Nomor Polisi', validators=[DataRequired()])
    sopir = StringField('Nama Sopir', validators=[DataRequired()])
    km_awal = IntegerField('KM Berangkat', validators=[DataRequired()])
    km_isi = IntegerField('KM Kembali')
    solar_awal = DecimalField('Solar Awal (L)')
    e_toll = IntegerField('E-Toll')
    tujuan = TextAreaField('Tujuan')
    keterangan = TextAreaField('Keterangan')
    foto = FileField('Tambahkan Foto', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Submit')

class IndexForm(FlaskForm):
    awal = DateField('Tgl Atas', validators=[DataRequired()])
    akhir = DateField('Bawah', validators=[DataRequired()])
    submit = SubmitField('Filter')

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    # page = request.args.get('page', 1, type=int)
    # list_laporan = Laporan.query.order_by(desc(Laporan.id)).paginate(page = page, per_page=50)
    return render_template("home.html", user=current_user)# , laporan=list_laporan)

@views.route('/api/data')
def data():
    query = Laporan.query.order_by(desc(Laporan.id))

    #search filter
    search = request.args.get('search')
    if search:
        query = query.filter(db.or_(
            Laporan.nopol.like(f'%{search}%'),
            Laporan.sopir.like(f'%{search}%')
        ))
    total = query.count()

    #sorting
    sort = request.args.get('sort')
    if sort:
        order = []
        for s in sort.split(','):
            direction = s[0]
            name = s[1:]
            if name not in ['tgl_brgkt','nopol', 'sopir']:
                name = 'id'
            col = getattr(Laporan, name)
            if direction == '-':
                col = col.desc()
            order.append(col)
        if order:
            query = query.order_by(*order)
    
    #pagination
    start = request.args.get('start', type=int, default=-1)
    length = request.args.get('length', type=int, default=-1)
    if start != -1 and length != -1:
        query = query.offset(start).limit(length)

    #response
    return {
        'data': [laporan.to_dict() for laporan in query],
        'total' : total}

# @views.route('/api/data/filtered')
# def filterd(tgl_atas, tgl_bwh):
#     query = Laporan.query.order_by(desc(Laporan.id)).filter(Laporan.tgl_brgkt<=datetime.strptime(tgl_atas,"%Y-%m-%d")+timedelta(days=1), Laporan.tgl_brgkt>=tgl_bwh)
    
#     #search filter
#     search = request.args.get('search')
#     if search:
#         query = query.filter(db.or_(
#             Laporan.nopol.like(f'%{search}%'),
#             Laporan.sopir.like(f'%{search}%')
#         ))
#     total = query.count()

#     #search filter
#     search = request.args.get('search')
#     if search:
#         query = query.filter(db.or_(
#             Laporan.nopol.like(f'%{search}%'),
#             Laporan.sopir.like(f'%{search}%')
#         ))
#     total = query.count()
    
#     #pagination
#     start = request.args.get('start', type=int, default=-1)
#     length = request.args.get('length', type=int, default=-1)
#     if start != -1 and length != -1:
#         query = query.offset(start).limit(length)

#     #response
#     return {
#         'data': [laporan.to_dict() for laporan in query],
#         'total' : total}


#detail laporan
@views.route('/laporan/<int:id>')
def laporan(id):
    laporan =  Laporan.query.get_or_404(id)
    foto = []
    if ImageSet.query.filter(ImageSet.laporan_id==id):
        for list in ImageSet.query.filter(ImageSet.laporan_id==id):
            foto.append(url_for('static', filename='images/laporan_images/' + list.image))

    return render_template('laporan.html', user=current_user, laporan=laporan, img=foto)

# upload img
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(views.root_path, 'static/images/laporan_images', picture_fn)
    output_size = (384, 216)
    
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

# tambah laporan berangkat
@views.route('/add-berangkat', methods=['POST','GET'])
@login_required
def add_berangkat():
    form = FormBerangkat()
    if form.validate_on_submit():
        nopol = form.nopol.data.upper()
        sopir = form.sopir.data.upper()
        satpam1 = form.satpam1.data.upper()
        km_awal = form.km_awal.data
        tujuan = form.tujuan.data
        file_foto = form.foto.data
        
        cek_nopol = Laporan.query.order_by(desc(Laporan.id)).filter_by(nopol=nopol).first()
            
        if cek_nopol:
            laporan = Laporan.query.get_or_404(cek_nopol.id)
            if laporan.tgl_kmbl==None:
                flash('Error! Nomor Polisi/Sopir belum kembali', category='error')          
            else:
                new_post = Laporan(tgl_brgkt=datetime.now().replace(microsecond=0), nopol=nopol, sopir=sopir, satpam1=satpam1, km_awal=km_awal, km_isi=0, solar_awal=0, e_toll=0, tujuan=tujuan)
                db.session.add(new_post)
                db.session.flush() #
                if file_foto:
                    foto = save_picture(file_foto)
                    new_foto = ImageSet(laporan_id=new_post.id, image= foto)
                    db.session.add(new_foto) #
                db.session.commit()
                return redirect(url_for('views.home'))
        else:
            new_post = Laporan(tgl_brgkt=datetime.now().replace(microsecond=0), nopol=nopol, sopir=sopir, satpam1=satpam1, km_awal=km_awal, km_isi=0, solar_awal=0, e_toll=0, tujuan=tujuan)
            db.session.add(new_post)
            db.session.flush() #
            if file_foto:
                foto = save_picture(file_foto)
                new_foto = ImageSet(laporan_id=new_post.id, image= foto)
                db.session.add(new_foto) #
            db.session.commit()
            return redirect(url_for('views.home'))
    return render_template("add_brgkt.html", title="Tambah Laporan Truk Berangkat", form = form, user=current_user)

# tambah laporan kembali
@views.route('/add-kembali', methods=['POST','GET'])
@login_required
def add_kembali():
    form = FormKembali()
    if form.validate_on_submit():
        nopol = form.nopol.data.upper()
        sopir = form.sopir.data.upper()
        satpam2 = form.satpam2.data.upper()
        km_isi = form.km_isi.data
        keterangan = form.keterangan.data
        file_foto = form.foto.data

        cek_nopol = Laporan.query.order_by(desc(Laporan.id)).filter_by(nopol=nopol).first()
        cek_sopir = Laporan.query.order_by(desc(Laporan.id)).filter_by(sopir=sopir).first()
        if cek_nopol and cek_sopir:
            laporan = Laporan.query.get_or_404(cek_nopol.id)
            if laporan.tgl_kmbl==None:
                laporan.satpam2 = satpam2
                laporan.tgl_kmbl = datetime.now().replace(microsecond=0)
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
            flash('Error! Nopol/Nama Sopir tidak ada', category='error')
    return render_template("add_kmbl.html", title="Tambah Laporan Truk Kembali", form = form, user=current_user)

@views.route('/laporan/<int:id>/update', methods=['GET', 'POST'])
@login_required
def update_laporan(id):
    laporan = Laporan.query.get_or_404(id)
    form = LaporanAdmin()
    file_foto = form.foto.data
    if form.validate_on_submit():
        laporan.nopol = form.nopol.data.upper()
        laporan.sopir = form.sopir.data.upper()
        laporan.km_awal = form.km_awal.data
        laporan.km_isi = form.km_isi.data
        laporan.solar_awal = form.solar_awal.data
        laporan.e_toll = form.e_toll.data
        laporan.tujuan = form.tujuan.data
        laporan.keterangan = form.keterangan.data
        if file_foto:
            foto = save_picture(file_foto)
            new_foto = ImageSet(laporan_id=laporan.id, image= foto)
            db.session.add(new_foto)
        db.session.commit()
        flash('Data laporan berhasil diupdate!', 'success')
        return redirect(url_for('views.laporan', id=laporan.id))
    elif request.method == 'GET':
        form.nopol.data = laporan.nopol
        form.sopir.data = laporan.sopir
        form.km_awal.data = laporan.km_awal
        form.km_isi.data = laporan.km_isi
        form.solar_awal.data = laporan.solar_awal
        form.e_toll.data = laporan.e_toll
        form.tujuan.data = laporan.tujuan
        form.keterangan.data = laporan.keterangan
    return render_template('add_admin.html', title="Update Laporan", form = form, user=current_user)

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
    list_laporan = Laporan.query.filter(Laporan.nopol==nopol).order_by(desc(Laporan.tgl_brgkt)).paginate(page = page, per_page=50)
    return render_template("home.html", user=current_user, laporan=list_laporan)

#list laporan berdasarkan sopir
@views.route('/sopir/<sopir>', methods=['GET'])
@login_required
def laporan_sopir(sopir):
    page = request.args.get('page', 1, type=int)
    list_laporan = Laporan.query.filter(Laporan.sopir==sopir).order_by(desc(Laporan.tgl_brgkt)).paginate(page = page, per_page=50)
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

