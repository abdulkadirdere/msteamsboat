import json
import logging
from os import environ

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    # get env variables
    HOOK_URL = environ.get("HookURL")
    env_name = environ.get("environmentName")

    # log url
    aws_log = 'https://af-south-1.console.aws.amazon.com/cloudwatch/home?region=af-south-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252F'

    message = json.loads(event['Records'][0]['Sns']['Message'])

    alarm_name = message['AlarmName']
    old_state = message['OldStateValue']
    new_state = message['NewStateValue']
    reason = message['NewStateReason']
    state_datetime = message["StateChangeTime"]
    func_name = message['Trigger']['Dimensions'][0]['value']
    log_path = aws_log + func_name

    # create base data for message type based on alarm type
    if new_state.lower() == 'alarm':
        data = {
            "colour": "d63333",
            "title": "Alert! There is an issue with **%s**." % alarm_name
        }
    elif new_state.lower() == 'ok':
        data = {
            "colour": "64a837",
            "title": "**%s** is resolved" % alarm_name
        }
    else:
        print("Unknown State")
        raise Exception("Error! Unknown State. Checkn the error logs")

    message = {
        "@context": "https://schema.org/extensions",
        "@type": "MessageCard",
        "themeColor": data["colour"],
        "title": data["title"],
        "text": "**%s** has changed from %s to %s." % (alarm_name, old_state, new_state),
        "sections": [
                {
                "title": "Details",
                "facts": [
                    {
                        "name": "Function Name",
                        "value": func_name
                    },
                    {
                        "name": "Enviroment",
                        "value": env_name
                    },
                    {
                        "name": "State Change Date/Time",
                        "value": state_datetime
                    },
                    {
                        "name": "Reason",
                        "value": reason
                    }
                ]
            }
          ],
        "potentialAction" : [
            {
                "@context": "http://schema.org",
                "@type": "ViewAction",
                "name": "View in AWS",
                "target": [log_path]
            }
            ]
    }

    req = Request(HOOK_URL, json.dumps(message).encode('utf-8'))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted")
        return 'Success'
    except HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return 'Failure'
    except URLError as url_err:
        logger.error(f"URL error occurred {url_err}")
        return 'Failure'
