
from numpy import double as npdouble
from numpy import array as nparray
from re import split as resplit

from Chandra.Time import DateTime


def read_eclipse_file(filename):

    def parse_line(line):
        words = line.split()
        starttime = words[0][4:] + ':' + words[0][:3] + ':' + words[1]
        stoptime = words[2][4:] + ':' + words[2][:3] + ':' + words[3]

        returndict = {'Start Time': starttime,
                      'Stop Time': stoptime,
                      'Duration': words[4],
                      'Current Condition': words[5],
                      'Obstruction': words[6],
                      'durationsec': npdouble(words[4]),
                      'startsec': DateTime(starttime).secs,
                      'stopsec': DateTime(stoptime).secs}

        if len(words) == 9:
            returndict.update({'Entry Timer': words[7],
                               'timersec': npdouble(words[7]),
                               'Type': words[8]})

        return returndict

    with open(filename, 'rb') as fid:
        datalines = fid.readlines()

    # The first line includes the year and day the file was generated
    #
    # Note: This entry may be manually created and could be a source of error
    # if read incorrectly.
    words = datalines.pop(0).split()
    #eclipse = {'epoch':dict(zip(('year','day'), (words[-2][:4],words[-2][5:])))}
    eclipse = {'epoch': {'year': words[2]}}
    eclipse['epoch'].update({'dom': words[0]})
    eclipse['epoch'].update({'month': words[1]})
    eclipse['epoch'].update({'time': words[3]})

    hosc = DateTime(words[2] + words[1] + words[0] + ' at ' + words[3]).date
    eclipse['epoch'].update({'doy': hosc[5:8]})

    # Remove spacing lines
    line = datalines.pop(0)
    while len(line.strip()) < 50:
        line = datalines.pop(0)

    headers = resplit("\s{2,5}", line.strip())

    # Truncate the Start Time, Stop Time and Duration header names
    headers[0] = headers[0][:10]
    headers[1] = headers[1][:9]
    headers[2] = headers[2][:8]

    # Remove the dashed lines separating the header from the eclipse data entries
    line = datalines.pop(0)

    # This is the eclipse number; it is used to index all eclipses in the
    # file. It has no other significance.
    n = -1
    eclipse.update({'eclipse_nums': []})

    while len(datalines) > 0:
        line = datalines.pop(0).strip()

        # All eclipse entries start wth at least 7 "words"
        if len(line.split()) == 7:

            # increment the eclipse number and create a placeholder dict
            n = n + 1
            eclipse['eclipse_nums'].append(n)
            eclipse.update({n: {}})

            # Add the entrance penumbra data, there will always be an entrance
            # penumbra
            eclipsedata = parse_line(line)
            eclipse[n].update({'entrancepenumbra': eclipsedata})

            # If this is a full eclipse, then there will also be umbra and
            # exit penumbra phases.
            if len(datalines) > 0:
                if 'Umbra' in datalines[0]:

                    line = datalines.pop(0)
                    eclipsedata = parse_line(line)
                    eclipse[n].update({'umbra': eclipsedata})

                    line = datalines.pop(0)
                    eclipsedata = parse_line(line)
                    eclipse[n].update({'exitpenumbra': eclipsedata})

    return eclipse


def convert_eclipse_times(eclipse):
    for n in eclipse['eclipse_nums']:
        if n != 'epoch':
            for m in eclipse[n].keys():
                eclipse[n][m].update({'durationsec':
                                      npdouble(eclipse[n][m]['Duration'])})
                eclipse[n][m].update({'startsec':
                                      DateTime(eclipse[n][m]['Start Time']).secs})
                eclipse[n][m].update({'stopsec':
                                      DateTime(eclipse[n][m]['Stop Time']).secs})
                if m == 'entrancepenumbra':
                    if eclipse[n][m].has_key('Entry Timer'):
                        eclipse[n][m].update({'timersec':
                                              npdouble(eclipse[n][m]
                                                       ['Entry Timer'])})
    return eclipse


def read_altitude(filename='altitude_prediction.txt'):
    fin = open(filename, 'rb')
    datalines = fin.readlines()
    fin.close()
    altitude = nparray([npdouble(line.strip().split()[1]) for line in datalines])
    times = nparray([DateTime(line.strip().split()[0]).secs for line in datalines])
    return (times, altitude)


def read_comms(filename, numheaderlines, year):

    fin = open(filename, 'rb')
    datalines = fin.readlines()
    fin.close()
    [datalines.pop(0) for n in range(numheaderlines)]

    year = str(year)

    fieldnames = ('day', 'start', 'bot', 'eot', 'end', 'facility', 'user',
                  'endocde2', 'endcode1', 'config', 'passno', 'activity',
                  'tstart', 'tbot', 'teot', 'tend')

    commdata = {}

    k = -1
    while len(datalines) > 0:
        if len(datalines[0].strip()) > 20:
            k = k + 1

            words = datalines.pop(0).strip().split()
            try:
                day = words.pop(0)
            except:
                import readline  # optional, will allow Up/Down/History in the console
                import code
                vars = globals().copy()
                vars.update(locals())
                shell = code.InteractiveConsole(vars)
                shell.interact()
            start = words.pop(0)
            bot = words.pop(0)
            eot = words.pop(0)
            end = words.pop(0)
            facility = words.pop(0)
            user = words.pop(0)
            endcode2 = words.pop(-1)
            endcode1 = words.pop(-1)
            config = words.pop(-1)
            passno = words.pop(-1)
            activity = ' '.join(words)

            yearday = year + ':' + day + ':'
            tstart = DateTime(yearday + start[:2] + ':' + start[2:] +
                              ':00.000').secs
            tbot = DateTime(yearday + bot[:2] + ':' + bot[2:] + ':00.000').secs
            teot = DateTime(yearday + eot[:2] + ':' + eot[2:] + ':00.000').secs
            tend = DateTime(yearday + end[:2] + ':' + end[2:] + ':00.000').secs

            if npdouble(bot) < npdouble(start):
                tbot = tbot + 24 * 3600
                teot = teot + 24 * 3600
                tend = tend + 24 * 3600
            elif npdouble(eot) < npdouble(bot):
                teot = teot + 24 * 3600
                tend = tend + 24 * 3600
            elif npdouble(end) < npdouble(eot):
                tend = tend + 24 * 3600

            passinfo = (day, start, bot, eot, end, facility, user, endcode2,
                        endcode1, config, passno, activity, tstart, tbot, teot,
                        tend)

            commdata.update(dict({k: dict(zip(fieldnames, passinfo))}))

        junk = datalines.pop(0)

    return commdata
