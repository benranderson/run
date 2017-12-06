deploy:
	git push origin master
	heroku maintenance:on
	git push heroku master
	heroku run flask deploy
	heroku restart
	heroku maintenance:off

resetdb:
	flask createdb --drop_first=True
	flask seeddb