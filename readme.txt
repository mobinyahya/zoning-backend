source SFUSD_UI_ENV/bin/activate # called from the PycharmProjects folder, activates the virtual env
echo $VIRTUAL_ENV
cd SFUSD-UI # enter the SFUSD-UI  project folder to be running the followings
flask run # runs the flask on local device to build the local host http://127.0.0.1:5000
git push heroku main #push everything on heroku and run it on the server


installed node: brew install node

do you keep react frontend in the same repo as backend?
how do front and back get connected on heroku?
I'm using axios, any thoughts/recommendations?
na fetch estefade kon: i.e. await fetch() [it is asynch]