from typing import Tuple

from flask import Flask, jsonify, request, Response, render_template, url_for
import mockdb.mockdb_interface as db
import requests

app = Flask(__name__)


def create_response(
    data: dict = None, status: int = 200, message: str = ""
) -> Tuple[Response, int]:
    """Wraps response in a consistent format throughout the API.
    
    Format inspired by https://medium.com/@shazow/how-i-design-json-api-responses-71900f00f2db
    Modifications included:
    - make success a boolean since there's only 2 values
    - make message a single string since we will only use one message per response
    IMPORTANT: data must be a dictionary where:
    - the key is the name of the type of data
    - the value is the data itself

    :param data <str> optional data
    :param status <int> optional status code, defaults to 200
    :param message <str> optional message
    :returns tuple of Flask Response and int, which is what flask expects for a response
    """
    if type(data) is not dict and data is not None:
        raise TypeError("Data should be a dictionary 😞")

    response = {
        "code": status,
        "success": 200 <= status < 300,
        "message": message,
        "result": data,
    }
    return jsonify(response), status


"""
~~~~~~~~~~~~ API ~~~~~~~~~~~~
"""


@app.route("/")
def hello_world():
    return create_response({"content": "hello world!"})


@app.route("/mirror/<name>/")
def mirror(name):
    data = {"name": name}
    return create_response(data)


@app.route("/users/", methods=["GET", "POST"])
def users():
    if request.method == "POST":
        if "name" in request.form and "age" in request.form and "team" in request.form:
            name = request.form["name"]
            age = request.form["age"]
            team = request.form["team"]
            if name.strip() != "" and team.strip() != "":
                try:
                    age = int(age)
                except ValueError:
                    return create_response(None, 422, "Cannot create new user because age is not a number")
                new_user = db.create("users", {"name": name, "age": age,
                                               "team": team})
                return create_response({"new user": new_user}, 201, f"user with id {new_user['id']} "
                                                                    f"has successfully been created")
        return create_response(None, 422, "Cannot create new user because user name, age and/or team are missing")
    else:
        team = request.args.get("team")
        if team:
            return create_response({"users": db.getUsersByTeam(team)}, 200, f"Users filtered by team {team}")
        else:
            return create_response({"users": db.get("users")}, 200, "")


@app.route("/users/<id>/", methods=["GET", "PUT", "DELETE"])
def user_by_id(id):
    id = int(id)
    user = db.getById("users", id)
    if not user:
        return create_response(None, 404, "There is no user associated with this id!")
    else:
        if request.method == "PUT":
            if "name" in request.form:
                name = request.form["name"]
                if name.strip() != "":
                    db.updateById("users", id, {"name": name})
            if "age" in request.form:
                age = request.form["age"]
            if type(age) == int or type(age) == str and age.strip() != "":
                if type(age) == str:
                    try:
                        age = int(age)
                    except ValueError:
                        return create_response(None, 422, "Cannot update user because age is not a number")
                db.updateById("users", id, {"age": age})
            if "team" in request.form:
                team = request.form["team"]
                if team.strip() != "":
                    db.updateById("users", id, {"team": team})
            return create_response({"user": db.getById("users", id)}, 200, f"user with id {id} "
                                                                               f"has successfully been updated")
        elif request.method == "DELETE":
            db.deleteById("users", id)
            return create_response(None, 200, f"user with id {id} has successfully been deleted")
        else:
            return create_response({"user": db.getById("users", id)}, 200, "")


# This route is to have a form on a separate page. Normally, the form would be added to the /users GET template
@app.route('/users/create_user/')
def create_user():
    return render_template('create_user.html')


# This route is to have a form on a separate page. Normally, the form would be added to the /users/<id> GET template.
# Accepting a post method like we do here which executes the put is messy and unRESTful but is a workaround to counter
# the limitation of HTML forms to get and post.
@app.route('/users/update_user/', methods=["GET", "POST"])
def update_user():
    if request.method == "POST":
        id = request.form["id"]
        if not id or id.strip() == "":
            return create_response(None, 404, "can't update user with blank id!")
        name = request.form["name"]
        age = request.form["age"]
        team = request.form["team"]
        url_root = request.url_root
        url_root = url_root[:-1]
        url_rest = url_for("user_by_id", id=id)
        r = requests.put(f"{url_root}{url_rest}", data={"name": name, "age": age, "team": team})
        return r.text, r.status_code
    else:
        return render_template('update_user.html')


# This route is to have a form on a separate page. Normally, the form would be added to the /users/<id> GET template.
# Accepting a post method like we do here which executes the put is messy and unRESTful but is a workaround to counter
# the limitation of HTML forms to get and post.
@app.route('/users/delete_user/', methods=["GET", "POST"])
def delete_user():
    if request.method == "POST":
        id = request.form["id"]
        if not id or id.strip() == "":
            return create_response(None, 404, "can't delete user with blank id!")
        url_root = request.url_root
        url_root = url_root[:-1]
        url_rest = url_for("user_by_id", id=id)
        r = requests.delete(f"{url_root}{url_rest}")
        return r.text, r.status_code
    else:
        return render_template('delete_user.html')


"""
~~~~~~~~~~~~ END API ~~~~~~~~~~~~
"""
if __name__ == "__main__":
    app.run(debug=True)
