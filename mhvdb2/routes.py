from mhvdb2 import app
from mhvdb2.models import Entity, Payment, User
from flask import render_template, request, flash, redirect, url_for
from mhvdb2.authentication import authenticate_user, register_user
from flask.ext.login import login_required, current_user, logout_user, current_app
from mhvdb2.resources import payments, members, entities
from datetime import datetime


def get_post_value(key):
    try:
        return request.form[key]
    except KeyError:
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/admin/login", methods=["GET"])
def login():
    # If there are no users, send them to the registration page
    if User.select().count() == 0:
        flash("No admins found, please register the first administrator.", "info")
        return redirect(url_for("register"))
    return render_template("admin/login.html")


@app.route("/admin/login", methods=["POST"])
def login_post():
    email = get_post_value("email")
    password = get_post_value("password")
    success = authenticate_user(email, password)
    if success:
        flash("Logged in successfully.", "success")
        next = request.args.get("next", '/')
        return redirect(next)
    else:
        flash("Incorrect email or password.", "danger")
        return render_template("admin/login.html", email=email)


@app.route("/admin/register", methods=["GET"])
def register():
    # Only allow access if logged in or no users are registered
    if current_user.is_anonymous() and User.select().count() > 0:
        return current_app.login_manager.unauthorized()

    return render_template("admin/register.html")


@app.route("/admin/register", methods=["POST"])
def register_post():
    # Only allow access if logged in or no users are registered
    if current_user.is_anonymous() and User.select().count() > 0:
        return current_app.login_manager.unauthorized()

    name = get_post_value("name")
    email = get_post_value("email")
    password = get_post_value("password")

    errors = register_user(name, email, password)
    if len(errors) > 0:  # This means that an error has occured
        for e in errors:
            flash(e, 'danger')
        return render_template("admin/register.html", name=name, email=email)
    else:
        flash("User registered successfully.", "success")
        return redirect(url_for('register'))


@app.route("/admin/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))


@app.route('/signup/', methods=['GET'])
def signup_get():
    return render_template('signup.html')


@app.route('/signup/', methods=['POST'])
def signup_post():
    name = get_post_value("name")
    email = get_post_value("email")
    phone = get_post_value("phone")

    errors = members.validate(name, email, phone)

    # Check if the "agree" checkbox was ticked
    if get_post_value("agree") is None:
        errors.append("You must agree to the rules and code of conduct to become a member!")

    if members.exists(email):
        errors.append("There is already a member with that email address!")

    if len(errors) > 0:  # This means that an error has occured
        for e in errors:
            flash(e, 'danger')

        return render_template('signup.html', name=name, email=email,
                               phone=phone), 400

    members.create(name, email, phone)
    flash("Thanks for registering!", "success")

    return signup_get()


@app.route('/payments/', methods=['GET'])
def payments_get():
    return render_template('payments.html')


@app.route('/payments/', methods=['POST'])
def payments_post():
    amount = get_post_value("amount")
    email = get_post_value("email")
    method = get_post_value("method")
    type = get_post_value("type")
    notes = get_post_value("notes")
    reference = get_post_value("reference")

    errors = payments.validate(amount, email, method, type, notes, reference)

    if len(errors) > 0:  # this means that an error has occured
        for e in errors:
            flash(e, 'danger')
        return render_template('payments.html', amount=amount, email=email,
                               method=method, type=type, notes=notes,
                               reference=reference), 400

    # Cajole the post data into integers
    amount = int(amount)
    type = int(type)
    method = int(method)

    payments.create(amount, email, method, type, notes, reference)
    flash("Thank you!", "success")

    return payments_get()


@app.route('/admin/')
@login_required
def admin():
    return render_template('admin.html')


@app.route('/admin/members')
@login_required
def admin_members():
    members = Entity.select().where(Entity.is_member)
    return render_template('admin/members.html', members=members)


@app.route('/admin/members/new', methods=['GET'])
@login_required
def member_new_get():
    return render_template('admin/member.html', new=True)


@app.route('/admin/members/new', methods=['POST'])
@login_required
def member_new_post():
    name = get_post_value("name")
    email = get_post_value("email")
    phone = get_post_value("phone")
    joined_date = get_post_value("joined_date")
    agreement_date = get_post_value("agreement_date")

    errors = members.validate(name, email, phone, joined_date, agreement_date)

    if members.exists(email):
        errors.append("There is already a member with that email address!")

    if len(errors) > 0:  # This means that an error has occured
        for e in errors:
            flash(e, 'danger')
        return render_template('admin/member.html', name=name, email=email, phone=phone,
                               joined_date=joined_date, agreement_date=agreement_date), 400

    joined_date = datetime.strptime(joined_date, '%Y-%m-%d').date()
    agreement_date = datetime.strptime(agreement_date, '%Y-%m-%d').date()

    members.create(name, email, phone, joined_date, agreement_date)
    flash("Member created", "success")

    return redirect(url_for('admin_members'))


@app.route('/admin/members/<int:member_id>', methods=['GET'])
@login_required
def member_get(member_id):
    member = members.get(member_id)
    if member:
        return render_template('admin/member.html', name=member.name, email=member.email,
                               phone=member.phone, joined_date=member.joined_date,
                               agreement_date=member.agreement_date)
    else:
        return redirect(url_for('admin_members'))


@app.route('/admin/members/<int:member_id>', methods=['POST'])
@login_required
def member_post(member_id):
    name = get_post_value("name")
    email = get_post_value("email")
    phone = get_post_value("phone")
    joined_date = get_post_value("joined_date")
    agreement_date = get_post_value("agreement_date")

    errors = members.validate(name, email, phone, joined_date, agreement_date)

    if members.exists(email, member_id):
        errors.append("There is already a member with that email address!")

    if len(errors) > 0:  # This means that an error has occured
        for e in errors:
            flash(e, 'danger')
        return render_template('admin/member.html', member_id=member_id, name=name, email=email,
                               phone=phone, joined_date=joined_date,
                               agreement_date=agreement_date), 400

    joined_date = datetime.strptime(joined_date, '%Y-%m-%d').date()
    agreement_date = datetime.strptime(agreement_date, '%Y-%m-%d').date()

    members.update(member_id, name, email, phone, joined_date, agreement_date)

    flash("Member updated", "success")

    return redirect(url_for('admin_members'))


@app.route('/admin/transactions')
@login_required
def admin_transactions():
    transactions = Payment.select()
    return render_template('admin/transactions.html', transactions=transactions)


@app.route('/admin/entities')
@login_required
def admin_entities():
    entities = Entity.select().where(Entity.is_member == False)          # noqa
    return render_template('admin/entities.html', entities=entities)


@app.route('/admin/entities/new', methods=['GET'])
@login_required
def entity_new_get():
    return render_template('admin/entity.html', new=True)


@app.route('/admin/entities/new', methods=['POST'])
@login_required
def entity_new_post():
    name = get_post_value("name")
    email = get_post_value("email")
    phone = get_post_value("phone")

    errors = entities.validate(name, email, phone)

    if len(errors) > 0:  # This means that an error has occured
        for e in errors:
            flash(e, 'danger')
        return render_template('admin/entity.html', new=True, name=name, email=email,
                               phone=phone), 400

    entity_id = entities.create(name, email, phone)
    flash("Entity created", "success")

    return redirect(url_for('entity_get', entity_id=entity_id))


@app.route('/admin/entities/<int:entity_id>', methods=['GET'])
def entity_get(entity_id):
    entity = entities.get(entity_id)
    if entity:
        return render_template('admin/entity.html', name=entity.name, email=entity.email,
                               phone=entity.phone)
    else:
        return redirect(url_for('admin_entities'))


@app.route('/admin/entities/<int:entity_id>', methods=['POST'])
@login_required
def entity_post(entity_id):
    name = get_post_value("name")
    email = get_post_value("email")
    phone = get_post_value("phone")

    errors = entities.validate(name, email, phone)

    if len(errors) > 0:  # This means that an error has occured
        for e in errors:
            flash(e, 'danger')
        return render_template('admin/entity.html', entity_id=entity_id, name=name, email=email,
                               phone=phone), 400

    entities.update(entity_id, name, email, phone)
    flash("Entity updated", "success")

    return redirect(url_for('admin_entities'))
