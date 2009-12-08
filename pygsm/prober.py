#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

def probe(verbose=False):
    """Searches for probable ports on the system"""
    import platform
    from gsmmodem import GsmModem
    import serial
    # Common baudrates in approximate popularity order
    baudrates = [115200, 9600, 19200]
    ports = []

    if platform.system() == 'Linux':
        import scanlinux as portscanner
    if platform.system() == 'Windows':
        import scanwin32 as portscanner
    if platform.system() == 'Darwin':
        import scanmac as portscanner

    try:
        for port in portscanner.scan():
            if verbose: print "Attempting to connect to port %s" % port
            try:
                for baudrate in baudrates:
                    if verbose:
                        GsmModem(port=port, timeout=10, 
                                baudrate=baudrate)
                    else:
                        GsmModem(port=port, timeout=10, 
                                logger=logger, baudrate=baudrate)
                    ports.append((port, baudrate))
                    # If a connection is made, ignore the less-likely
                    # baudrates
                    break
            except serial.serialutil.SerialException, e:
                if verbose: print e
                pass
    except NameError, e:
        if verbose: print e
        pass
    return ports

def logger(_modem, message_, type_):
    """Supress all output from pySerial and gsmmodem"""
    pass

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-v', '--verbose', action='store_true',
            dest='verbose', default=False,
            help='Display modem debug messages')
    (options, args) = parser.parse_args()
    print "\n".join(
            map(repr, probe(verbose=options.verbose)))
