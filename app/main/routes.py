from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response, make_response
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from app import db
from app.main.forms import EditProfileForm, SearchForm, NewClientForm, NewQuoteForm, ClientSearchForm, ItemForm
from app.models import User, Post, Notification, Quote, Company, Client, Item
from app.translate import translate
from app.main import bp
import pdfkit
import logging
import os

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    company = Company.query.filter_by(id=current_user.company_id).first()
    quotes = company.quotes.order_by(Quote.last_updated.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=quotes.next_num) \
        if quotes.has_next else None
    prev_url = url_for('main.index', page=quotes.prev_num) \
        if quotes.has_prev else None
    return render_template('index.html', title=_('Home'),
                           quotes=quotes.items, next_url=next_url,
                           prev_url=prev_url)



@bp.route('/user')
@login_required
def users():
    page = request.args.get('page', 1, type=int)
    users = current_user.company_users().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=users.next_num) \
        if users.has_next else None
    prev_url = url_for('main.index', page=users.prev_num) \
        if users.has_prev else None
    return render_template('users.html', title=_('Users'),
                           users=users.items, next_url=next_url,
                           prev_url=prev_url)



@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)



@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/client', methods=['GET', 'POST'])
@login_required
def clients():
    form = NewClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            representative_name=form.representative_name.data,
            phone=form.phone.data,
            email=form.email.data
        )
        client.company_id = current_user.company_id
        db.session.add(client)
        db.session.commit()
        flash(_('New client added!'))
        return redirect(url_for('main.clients'))
    page = request.args.get('page', 1, type=int)
    clients = current_user.company_clients().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=clients.next_num) \
        if clients.has_next else None
    prev_url = url_for('main.index', page=clients.prev_num) \
        if clients.has_prev else None
    return render_template('clients.html', title=_('Clients'),
                           clients=clients.items, next_url=next_url,
                           prev_url=prev_url, form=form)


@bp.route('/client/<id>', methods=['GET', 'POST'])
@login_required
def client(id):
    client = Client.query.filter_by(id=id).first()
    form = NewClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            representative_name=form.representative_name.data,
            phone=form.phone.data,
            email=form.email.data
        )
        client.name = form.name.data
        client.representative_name = form.representative_name.data
        client.phone = form.phone.data
        client.email = form.email.data
        db.session.commit()
        flash(_('Client edited!'))
        return redirect(url_for('main.client', id=id))
    elif request.method == 'GET':
        form.name.data = client.name
        form.representative_name.data = client.representative_name
        form.phone.data = client.phone
        form.email.data = client.email
    if client is None:
        flash(_('The client with this id was not found!'))
        return redirect(url_for('main.clients'))
    return render_template('client.html', form=form)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


@bp.route('/quotes')
@login_required
def quotes():
    page = request.args.get('page', 1, type=int)
    quotes = current_user.company_quotes().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=quotes.next_num) \
        if quotes.has_next else None
    prev_url = url_for('main.index', page=quotes.prev_num) \
        if quotes.has_prev else None
    return render_template('quotes.html', title=_('Quotes'),
                           quotes=quotes.items, next_url=next_url,
                           prev_url=prev_url)

@bp.route('/new_quote', methods=('GET','POST'))
@login_required
def new_quote():
    quoteform = NewQuoteForm()
    clientform = ClientSearchForm()
    itemform = ItemForm()
    company = Company.query.filter_by(id=current_user.company_id).first()
    clients = current_user.company_clients()
    return render_template(
        'quote/main.html',
        quoteform=quoteform,
        clientform=clientform,
        itemform=itemform,
        company=company,
        clients=clients,
        itemid=1
    )

@bp.route('/client_autocomplete')
@login_required
def client_autocomplete():
    clients = Client.query.filter_by(company_id=current_user.company_id).order_by(Client.name.asc()).all()
    return jsonify([e.name for e in clients])


@bp.route('/client_api', methods=['POST'])
@login_required
def client_api():
    client = Client.query.filter_by(name=request.form["name"]).first()
    if client is None:
        return jsonify(error=404)
    return jsonify(client.serialize())

@bp.route('/item', methods=['POST'])
@login_required
def new_item():
    return render_template('quote/_item.html', itemid=int(request.form["id"]))


@bp.route('/quote', methods=['POST'])
@login_required
def save_quote():
    logging.warning("Json is here")
    quote = request.get_json(force=True)
    company_id = quote["company_id"]
    client_id = int(quote["client_id"])
    items = quote["items"]
    object_name = quote["object_name"]
    total = float(quote["total"])
    vat = float(quote["vat"])
    totalwithwat = float(quote["totalwithvat"])
    newquote = Quote(
        client_id=client_id,
        company_id=company_id,
        user_id=current_user.id,
        object_name=object_name,
        total=total,
        vat=vat,
        totalwithvat=totalwithwat
    )
    db.session.add(newquote)
    db.session.commit()
    quote_id = newquote.id
    for item in items:
        if item["is_category"]:
            newitem = Item(
                quote_id=quote_id,
                name=item["name"],
                description=item["description"],
                is_category=True
            )
        else:
            newitem = Item(
                quote_id=quote_id,
                name=item["name"],
                description=item["description"],
                unit=item["unit"],
                price_per_unit=float(item["price"]),
                units=float(item["units"])
            )
        db.session.add(newitem)
        db.session.commit()
    return jsonify(error=200)



@bp.route('/quotetest')
def quotetest():
    quotes = [quote.serialize() for quote in Quote.query.all()]
    return jsonify(quotes)


@bp.route('/itemtest')
def itemtest():
    items = [item.serialize() for item in Item.query.all()]
    return jsonify(items)

@bp.route('/quote/<id>')
def pdftest(id):
    quote = Quote.query.filter_by(id=id).first()
    company = Company.query.filter_by(id=quote.company_id).first()
    client = Client.query.filter_by(id=quote.client_id).first()
    user = User.query.filter_by(id=quote.user_id).first()
    rendered = render_template('quote/pdf.html',
                           quote=quote,
                           company=company,
                           client=client,
                           user=user
                           )

    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    css = ['app/static/css/bootstrap.css']
    options = {
        '--viewport-size': '1024x768'
    }
    pdf = pdfkit.from_string(rendered, False, css=css, configuration=config, options=options)
    print(pdf)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = "inline; filename=test.pdf"
    return response, 200