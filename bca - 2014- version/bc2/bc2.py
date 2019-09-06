import argparse, tables, re, json, itertools
import numpy as np
import pandas as pd

h5filters = tables.Filters(complevel=1, complib='zlib')

def read_zz_components(config):
    """Returns a generator that returns a dictionary of each zone-to-zone
    benefit component.

    """

    # Grumble, grumble, Python 2.6 and stupid nested context managers
    # Too lazy to wrap this with 'with' until Py27
    base = tables.open_file(config["baseline"]["filepath"])
    alt = tables.open_file(config["alternative"]["filepath"])

    # Benefits by Period:
    for per in config["timeperiods"]["periods"]:
        period = per["period"]
        code = per["code"]
        trperiod = per["trperiod"]
        trcode = per["trcode"]
        assignper = per["assignper"]

        for zzben in config["benefits-by-period"]:
            cp = zzben["costpath"]
            vp = zzben["volumepath"]

            # Substitute various time period placeholders
            cp = cp.replace("${PER}",period)
            cp = cp.replace("${CODE}",code)
            cp = cp.replace("${TRPER}",trperiod)
            cp = cp.replace("${TRCODE}",trcode)
            cp = cp.replace("${ASSIGNPER}",assignper)

            vp = vp.replace("${PER}",period)
            vp = vp.replace("${CODE}",code)
            vp = vp.replace("${TRPER}",trperiod)
            vp = vp.replace("${TRCODE}",trcode)
            vp = vp.replace("${ASSIGNPER}",assignper)

            zzben["basecost"] = base.getNode(cp).read()
            zzben["basevol"] = base.getNode(vp).read()
            zzben["altcost"] = alt.getNode(cp).read()
            zzben["altvol"] = alt.getNode(vp).read()
            zzben["timeperiod"] = period

            if "description" not in zzben.keys():
                zzben["description"] = "%s %s" % (zzben["timeperiod"],
                                                  zzben["userclass"])
            else:
                pass

            yield zzben

    base.close()
    alt.close()

def calc_zz_benefit(zzben):
    """Calculate consumer surplus benefits based on costs and volumes of
    two scenarios. Takes a benefit component dictionary containing
    cost and volume arrays of both scenarios, as returned by
    read_zz_components(). Returns the calculated benefit as an array.

    """

    bc = zzben["basecost"]
    bv = zzben["basevol"]
    ac = zzben["altcost"]
    av = zzben["altvol"]

    rawben = (bc - ac) * ((bv + av) / 2)

    return(rawben)

def calc_zz_benefits(zzbens):
    """Returns a generator that returns a dictionary containing the
    calculated raw benefit for each benefit component.

    """
    for zzben in zzbens:
        rawben = calc_zz_benefit(zzben)
        zzben["rawben"] = rawben
        yield zzben

def calc_zz_dollar_benefits(zzbens, config):
    """Returns a generator that returns a dictionary containing calculated
    benefit (in dollars) for each benefit component. Takes a list of
    zone-to-zone benefit dictionaries and a dictionary containing the
    appropriate unit conversions.

    """

    for zzben in zzbens:
        dollarben = to_dollars(zzben, config)
        zzben["dollarben"] = dollarben
        yield zzben

def to_dollars(ben, config):
    """Converts raw benefits of a given unit type to dollars. Takes a
    benefit dictionary containing the raw benefit, and returns a
    dictionary with the dollar benefits array calculated. Should work
    for all benefit types.

    """

    userclass = ben["userclass"]
    timeperiod = ben["timeperiod"]
    benarray = ben["rawben"]
    try:
        units = ben["costunits"]
    except:
        units = "minutes"

    # If this starts getting hairy, separate conversion functions
    # might be wise
    if units == "minutes":
        conv = config["vot"][userclass][timeperiod] / 60.0
    elif units == "cents":
        conv = 0.1
    elif units == "dollars":
        conv = 1.0 # could simply return, but this is more an example
    else:
        raise ValueError(units + " is not a valid unit type")

    return(benarray * conv)

def all_dollar_benefits(config):
    """Returns all benefit component dictionaries (zone-to-zone, and
    eventually zone, link) in dollars.

    """

    zzdollars = calc_zz_dollar_benefits(
        calc_zz_benefits(read_zz_components(config)), config)

    allbens = itertools.chain(
        zzdollars) # plus other zonal, link benefits eventually

    return(allbens)

def shortdescription(benefit):
    """Takes a benefit component, and tries to make an H5-appropriate node
    name. Returns an ASCII string.

    """
    # Name things consistently as <userclass>_<timeperiod>, no spaces,
    # no non-alphanumeric chars (except underscores).

    messydesc = benefit['userclass'] + '_' + benefit['timeperiod']
    desc = re.sub(r'[\W]+', '', messydesc.encode('ascii'))
    return(desc)

def write_benefits_tabular(outputpath, benefits, benefittype="dollarben",
                           fmt="h5"):
    """Takes a benefit component, and returns a "long" set of tuples,
    suitable for appending to a pandas table object.

    """

    # This silly stuff isn't needed with up-to-date pandas. You can
    # simply do df.to_FOO()
    if fmt == "h5":
        store = pd.HDFStore(outputpath)
    else:
        pass

    csv_head = True # Write header the first time only

    for benefit in benefits:
        # Reshape the array
        widearr = benefit[benefittype]
        dim = widearr.shape[0] # assumes margins are the same
        longarr = widearr.reshape(-1)
        uc = benefit["userclass"].encode("ascii")
        tp = benefit["timeperiod"].encode("ascii")

        # build the zone-zone index, annoying that python has no
        # flatten()
        o,d = zip(* itertools.product(range(1, dim + 1), repeat=2))

        # zip() for long arrays appears to be slooow. Thankfully,
        # pandas isn't slow. As a side benefit, storing pandas is easy
        # too.
        df = pd.DataFrame({ 'origin' : o,
                            'destination' : d,
                            benefittype : longarr,
                            "userclass" : uc,
                            "timeperiod" : tp})


        print("writing %s %s %s" %
              (benefit["timeperiod"],
               benefit["userclass"],
               benefittype))

        if fmt == "csv":
            with open(outputpath, 'a') as f:
                df.to_csv(f, header=csv_head, append=True)
                csv_head = False
        else:
            store.append(benefittype, df, complib="zlib", complevel=1)





def write_benefits(outputpath, benefits, benefittype="dollarben"):
    """Writes computed benefits to HDF5 output path. Takes a string of an
    output path, a list of benefit component dictionaries, and a
    string denoting which benefit type (e.g. "dollarben") to write.

    """

    with tables.open_file(outputpath, mode='a', filters=h5filters) as output:
        # will fail if trying to overwrite an existing file; this is
        # by design.
        grp = output.createGroup("/", "benefits")

        for benefit in benefits:
            bname = shortdescription(benefit)
            barray = benefit[benefittype]
            print("writing %s %s %s" %
              (benefit["timeperiod"],
               benefit["userclass"],
               benefittype))
            a = output.createArray(grp, bname, barray)
            a.attrs.description = benefit['description']
            a.attrs.userclass = benefit['userclass']
            a.attrs.timeperiod = benefit['timeperiod']



if __name__ == '__main__':
    # Set up some command line options
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output",
                        help="Optional output file")

    parser.add_argument("-a", "--alternative",
                        help="""Optional alternative scenario;
                        overrides config.""")

    parser.add_argument("-b", "--baseline",
                        help="Optional baseline scenario; overrides config.")

    parser.add_argument("-c", "--config", required=True,
                        help="""JSON configuration file; defines scenario
                        parameters and user benefit components.""")

    parser.add_argument("-t", "--tabular",
                        help="""Write benefits in tabular format.""")

    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    if args.output:
        config["outputpath"] = args.output
    else: pass

    if args.alternative:
        config["alternative"]["filepath"] = args.alternative
    else: pass

    if args.baseline:
        config["baseline"]["filepath"] = args.baseline


    bens = all_dollar_benefits(config)

    if args.tabular == "csv":
        write_benefits_tabular(config["outputpath"], bens, fmt="csv")
    elif args.tabular == "h5":
        write_benefits_tabular(config["outputpath"], bens, fmt="h5")
    else:
        write_benefits(config["outputpath"], bens)
