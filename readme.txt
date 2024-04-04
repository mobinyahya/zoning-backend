source SFUSD_UI_ENV/bin/activate # called from the PycharmProjects folder, activates the virtual env
echo $VIRTUAL_ENV #if you want to see what virtual env you are using now
cd zoning-backend # enter the zoning-backend  project folder to be running the followings
flask run # runs the flask on local device to build the local host http://127.0.0.1:5000
git push heroku main #push everything on heroku and run it on the server
python requests_handler.py # to run the zone assignments
pip freeze > requirements.txt #to add all the installed libraries into the requirements file, for server to download them as well
