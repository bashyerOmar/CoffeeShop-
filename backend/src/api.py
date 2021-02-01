import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''

#db_drop_and_create_all()

# ROUTES
# show all drinks for public users , barista and manager 
@app.route('/drinks') 
def get_all_drinks():  
    # fetch all drinks from db 
    all_drinks=db.session.query(Drink).all()
    # print(all_drinks)
    if all_drinks is None:
       abort(404)
    else:
        # format drinks data as JSON 
        formmated_drinks=[Drink.short(drink) for drink in all_drinks]
        return jsonify({
            'success': True,
            'drinks':formmated_drinks
        }), 200 
    


@app.route('/drinks-detail')
# permission here for Barista and Manager 
@requires_auth('get:drinks-detail')
def get_drinks_with_details(payload_token):
    # fetch all drinks from db 
    all_drinks=db.session.query(Drink).all()
    # print(all_drinks)
    if all_drinks is None:
       abort(404)
    else:
        # format drinks data as JSON 
        formmated_drinks=[Drink.long(drink) for drink in all_drinks]
        return jsonify({
            'success': True,
            'drinks':formmated_drinks 
        }), 200 


@app.route('/drinks' , methods=['POST'])
# permission here for Manager only
@requires_auth('post:drinks')
def add_new_drink(payload_token):
    drink_data=request.json

    if not drink_data:
        abort(400)

    title = drink_data["title"]
    recipe = drink_data["recipe"]
    # create new drink object
    new_drink=Drink(title=title , recipe=json.dumps(recipe)) # convert recipe to string
    
    # insert new drink to db 
    Drink.insert(new_drink) 

    new_formmated_drink=Drink.long(new_drink) 
    return jsonify ({
           'success':True,
           'drinks':[new_formmated_drink] # array

        }), 200

    
         


@app.route('/drinks/<int:drink_id>',  methods=['PATCH'])
# permission here for Manager only
@requires_auth('patch:drinks')
def change_some_drink_details(payload_token, drink_id):
    # fetch data of the required drink 
    drink_to_update=db.session.query(Drink).filter(Drink.id == drink_id).one_or_none()
    if not drink_to_update:
        abort(404)

    updated_drink_data=request.json
    if not updated_drink_data:
        abort(400)
    # check if there is new value for title
    if "title" in updated_drink_data:
       new_title=updated_drink_data["title"]
       #replace new title with the old one
       drink_to_update.title = new_title
    # check if there is new value for recipe 
    if "recipe" in updated_drink_data:
        new_recipe=updated_drink_data["recipe"]
        #replace new recipe with the old one
        drink_to_update.recipe = json.dumps(new_recipe) # convert recipe to string
 
    Drink.update(drink_to_update)
    formmated_drink=Drink.long(drink_to_update)
    return jsonify({
           'success':True,
           'drinks':[formmated_drink]

        }), 200

    



@app.route('/drinks/<int:drink_id>' ,  methods=['DELETE'])
# permission here for Manager only
@requires_auth('delete:drinks')
def remove_drink(payload_token, drink_id):
    drink_to_delete=db.session.query(Drink).filter(Drink.id == drink_id).one_or_none()
    if drink_to_delete is None:
        abort(404)
    else:
        Drink.delete(drink_to_delete)
    
    return jsonify({
           'success':True,
           'delete':drink_id
        }), 200




# Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "unprocessable"
      }), 422
           

@app.errorhandler(404)
def not_found(error):
    return jsonify({
      "success": False, 
      "error": 404,
      "message": "resource not found"
      }), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
      "success": False, 
      "error": 400,
      "message": "Bad Request"
      }), 400


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
      "success": False,
      "error": 405,
      "message": "Method Not Allowed"
      }), 405

@app.errorhandler(500)
def not_found(error):
    return jsonify({
      "success": False, 
      "error": 500,
      "message": "internal server error"
      }), 500

#to handle 403 and 401 
@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code

