# Authors: Antonis Gotsis (Feron Technologies P.C.)
# License: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
# Developed for use by the EU H2020 MONROE OC2 MOVEMENT project
# Summary: A class implementing packet sniffer

import threading   # needed for running metadata retrieval as thread within the main program
import sys         # needed for debugging purposes
import time        # needed for managing time
import pcapy       # for packet sniffing

class sniffer_thread(threading.Thread):
	def __init__(self, iface, logger, name='SnifferThread'):
		self._stopevent = threading.Event()
		threading.Thread.__init__(self, name=name)
		# set parameters
		self.logger = logger
		self.iface = iface

	def terminate(self):
		 self._stopevent.set()

	def run(self):
		self.logger.info('Started packet sniffing thread for device ' + self.iface + ', at ' + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time())))
		cap = pcapy.open_live(self.iface , 65536 , 1 , 0)
		while not self._stopevent.isSet():
			(header, packet) = cap.next()
			self.logger.info('\t[SNIFFER] Captured %d bytes' %(header.getlen()))
			#parse_packet(dev, packet, snifferlogger)

		# finalization actions after stop event
		self.logger.info('Gracefully exit sniffer thread at ' + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time())))
