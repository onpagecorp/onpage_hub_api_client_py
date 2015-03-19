#!/usr/bin/python

import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger(__name__)
logging.getLogger('suds.client').setLevel(logging.ERROR)

from onpage_hub_api_client.Message import Message
from onpage_hub_api_client.OnPageHubApi import OnPageHubApi
from onpage_hub_api_client.Configuration import Configuration
import optparse


def no_log(p):
    pass


def log(level, message):
    global logger
    try:
        log_by_level = {
            logging.INFO: logger.info,
            logging.ERROR: logger.error,
            logging.CRITICAL: logger.critical,
            logging.DEBUG: logger.debug,
            logging.WARN: logger.warn,
            logging.WARNING: logger.warning,
            logging.FATAL: logger.fatal,
            logging.NOTSET: no_log
        }

        log_by_level[level](message)
    except Exception, e:
        print e


def check_parameters(command_line_parser, options):
    log(logging.DEBUG, 'check_parameters() start...')
    configuration = Configuration()

    if not options.user:
        options.user = configuration.get_enterprise_from_configuration()

    if not options.user:
        error_message = 'Specify -u|--user parameter'
        log(logging.ERROR, error_message)
        command_line_parser.error(error_message)

    if not options.token:
        options.token = configuration.get_token_from_configuration()

    if not options.token:
        error_message = 'Specify -t|--token parameter'
        log(logging.ERROR, error_message)
        command_line_parser.error(error_message)

    if not options.subject:
        error_message = 'Specify -s|--subject parameter'
        log(logging.ERROR, error_message)
        command_line_parser.error(error_message)

    if not options.recipients:
        error_message = 'Specify -r|--recipients parameter'
        log(logging.ERROR, error_message)
        command_line_parser.error(error_message)

    if not options.sender:
        error_message = 'Specify -f|--from parameter'
        log(logging.ERROR, error_message)
        command_line_parser.error(error_message)

    log(logging.DEBUG, 'check_parameters() end.')


def configure_logger(options):
    log_level = getattr(logging, options.log_level.upper())

    rotating_file_log_handler = TimedRotatingFileHandler("sendOnPage.log", when="midnight")
    rotating_file_log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s:%(message)s'))

    console_log_handler = logging.StreamHandler()
    console_log_handler.setFormatter(logging.Formatter('%(message)s'))

    global logger
    logger.addHandler(rotating_file_log_handler)
    logger.addHandler(console_log_handler)

    logger.setLevel(log_level)


def parse_command_line():
    command_line_parser = optparse.OptionParser(usage='usage: %prog \n\t'
                                                      '-u|--user user_name\n\t'
                                                      '-t|--token token\n\t'
                                                      '-s|--subject subject\n\t'
                                                      '-r|--recipients recipient_1[,recipient_2[,...]]\n\t'
                                                      '-f|--from sender_name\n\t'
                                                      '[-m|--m message_body]\n\t'
                                                      '[-l|--log INFO|NOTSET|DEBUG|ERROR|CRITICAL|FATAL]\n')

    command_line_parser.add_option("-u", "--user", action="store", type="string", dest="user")
    command_line_parser.add_option("-t", "--token", action="store", type="string", dest="token")
    command_line_parser.add_option("-s", "--subject", action="store", type="string", dest="subject")
    command_line_parser.add_option("-r", "--recipients", action="store", type="string", dest="recipients")
    command_line_parser.add_option("-f", "--from", action="store", type="string", dest="sender")
    command_line_parser.add_option("-m", "--message", action="store", type="string", dest="message", default='')
    command_line_parser.add_option("-l", "--log", action="store", type="string", dest="log_level", default='INFO')
    options, args = command_line_parser.parse_args()

    configure_logger(options)

    check_parameters(command_line_parser, options)

    return options


def generate_message(options):
    log(logging.DEBUG, 'generate_message() start...')

    list_of_messages = []

    from random import randrange
    from time import gmtime, strftime

    message = Message()
    message.messageId = '' + strftime('%d%m%y%H%M%S', gmtime()) + '-' + str(randrange(1000, 10000))
    message.sender = options.sender
    message.subject = options.subject
    message.body = options.message
    message.recipients = options.recipients.split(',')
    message.replyOptions = []
    message.callbackUrl = None

    list_of_messages.append(message)

    log(logging.DEBUG, 'generate_message() end.')

    return list_of_messages


def send_message(options):
    log(logging.DEBUG, 'send_message() start...')

    list_of_messages = generate_message(options)

    onpage_hub_api_proxy = OnPageHubApi('https://qanps.onpage.com/hub-api?wsdl', options.user, options.token)

    result = onpage_hub_api_proxy.sendPage(list_of_messages)
    log(logging.DEBUG, result)

    check_status = result['Messages'][0][0]

    if check_status['ACCEPTED']:
        log(logging.INFO, "Message " + check_status.id + ' accepted by OnPage')
    else:
        log(logging.INFO,
            "Message " + check_status.id +
            ' was not accepted by OnPage: (' +
            str(check_status.ERROR_CODE) + ') ' +
            check_status.ERROR_DESCRIPTION)

    log(logging.DEBUG, 'send_message() end.')


def main():
    options = parse_command_line()

    send_message(options)


if __name__ == "__main__":
    main()
