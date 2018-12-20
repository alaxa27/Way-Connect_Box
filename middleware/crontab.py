from utils import get_crons, save_crons, write_crons
from utils import CrontabExecutionFailed, CronWritingError, GetCronError


class ApplyCrontabError(Exception):
    pass


def apply_crontab(config, cronFile):
    print('Retrieving crons from config...', end='')
    try:
        crons = get_crons(config)
    except GetCronError as e:
        print('FAIL')
        raise ApplyCrontabError(e)
    print('OK')

    print('Writing crons to cronjob file...', end='')
    try:
        write_crons(crons, cronFile)
    except CronWritingError as e:
        print('FAIL')
        raise ApplyCrontabError(e)
    print('OK')
    
    print('Saving new crons...', end='')
    try:
        save_crons(cronFile)
    except CrontabExecutionFailed as e:
        print('FAIL')
        raise ApplyCrontabError(e)
    print('OK')
