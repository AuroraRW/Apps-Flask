from flask import Flask, g, request, jsonify
from database import get_db
from functools import wraps

app = Flask(__name__)

api_username = 'admin'
api_password = 'password'


def protected(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and auth.username == api_username and auth.password == api_password:
            return f(*args, **kwargs)
        return jsonify({'message': 'Authorization failed! '}), 401
    return decorated


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite3'):
        g.sqlite_db.close()


@app.route('/member', methods=['GET'])
@protected
def get_members():
    db = get_db()
    members_cur = db.execute('select id, name, email, level from members')
    members = members_cur.fetchall()

    result = []
    for member in members:
        member_dict = {}
        member_dict['id'] = member['id']
        member_dict['name'] = member['name']
        member_dict['email'] = member['email']
        member_dict['level'] = member['level']
        result.append(member_dict)

    return jsonify({'members': result})


@app.route('/member/<int:member_id>', methods=['GET'])
@protected
def get_member(member_id):
    db =get_db()
    cur = db.execute('select id, name, email, level from members where id=?', [member_id])
    result = cur.fetchone()

    return jsonify({'member': {'id': result['id'], 'name': result['name'], 'email': result['email'], 'level': result['level']}})


@app.route('/member', methods=['POST'])
@protected
def add_member():
    new_member = request.get_json()
    name = new_member['name']
    email = new_member['email']
    level = new_member['level']

    db = get_db()
    db.execute('insert into members (name, email, level) values (?, ?, ?)', [name, email, level])
    db.commit()

    member_cur = db.execute('select id, name, email, level from members where name = ?', [name])
    member = member_cur.fetchone()

    return jsonify({'member': {'id': member['id'], 'name': member['name'], 'email': member['email'], 'level': member['level']}})


@app.route('/member/<int:member_id>', methods=['PUT', 'PATCH'])
@protected
def edit_member(member_id):
    new_member = request.get_json()
    name = new_member['name']
    email = new_member['email']
    level = new_member['level']

    db = get_db()
    db.execute('update members set name=?, email=?, level=? where id=?', [name, email, level, member_id])
    db.commit()

    member_cur = db.execute('select id, name, email, level from members where id = ?', [member_id])
    member = member_cur.fetchone()

    return jsonify(
        {'member': {'id': member['id'], 'name': member['name'], 'email': member['email'], 'level': member['level']}})


@app.route('/member/<int:member_id>', methods=['DELETE'])
@protected
def delete_member(member_id):
    db = get_db()
    db.execute('delete from members where id=?', [member_id])
    db.commit()

    return jsonify({'message': 'The member has been deleted!'})


if __name__ == '__main__':
    app.run()
