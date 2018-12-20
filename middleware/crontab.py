import subprocess


class ApplyCrontabError(Exception):
    pass


class CrontabExecutionFailed(Exception):
    pass


class CronWritingError(Exception):
    pass


class GetCronError(Exception):
    pass


def apply_crontab(config, cronFile):
    print('Retrieving crons from config...', end='')
    try:
        crons = get_crons(config)
    except GetCronError:
        print('FAIL')
        raise ApplyCrontabError()
    print('OK')

    print('Writing crons to cronjob file...', end='')
    try:
        write_crons(crons, cronFile)
    except CronWritingError:
        print('FAIL')
        raise ApplyCrontabError()
    print('OK')
    
    print('Saving new crons...', end='')
    try:
        save_crons(cronFile)
    except CrontabExecutionFailed:
        print('FAIL')
        raise ApplyCrontabError()
    print('OK')


def get_crons(config):
    crons = []
    for key, value in config.items():
        if key.startswith('CRON_'):
            crons.append(value)
    return crons


def write_crons(crons, file):
    with open(file, 'w') as file:
        for cron in crons:
            try:
                file.write(f'{cron}\n')
            except IOError:
                raise CronWritingError()


def save_crons(file):
    try:
        subprocess.check_call(['sudo', '/usr/bin/crontab', file])
    except OSError:
        raise CrontabExecutionFailed()
    except subprocess.SubprocessError:
        raise CrontabExecutionFailed()
