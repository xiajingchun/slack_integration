# slack_integration
a slack app to forward messages to MS teams and Dingtalk

## install dependencies

```
pip install flask
pip install requests
pip install slack-sdk
pip install gunicorn
```
## set env

```
export SLACK_SIGNING_SECRET=
export SLACK_BOT_TOKEN=
export TEAMS_WEBHOOK_URL=
export DINGTALK_WEBHOOK_URL=

```
## run it

```
gunicorn postman:app
```

## other settings
* create a slack app https://api.slack.com/
* install it to the relevant slack channel


