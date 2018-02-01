"""
VoIP Packet Capture
Feron Technologies P.C.
Packet Capturing Tool for VoIP traffic
"""

import datetime
import dpkt
import pcapy
import socket
from struct import *
import sys
import numpy as np
import time
import pyping


class VoipPacketCapture(object):
	"""
	VoIP Packet Capture Class
	"""

	ETH_PROTOCOL_ID  = 8
	ICMP_PROTOCOL_ID = 1
	TCP_PROTOCOL_ID  = 6
	UDP_PROTOCOL_ID  = 17

	ETH_HEADER_SIZE  = 14
	IP_HEADER_SIZE   = 20

	rtp_seq_list  = []
	rtp_sent_timestamp_list  = []
	rtp_rec_time_list  = []
	rtp_delta_list  = []
	rtp_jitter_list  = []
	rtp_interarrival_list  = []
	rtp_jitter2_list  = []
	jitter_ms = 0
	packet_loss_perc = 0
	latency_ms_list = []

	def __init__(self):
		return

	def __conv_eth_addr(self, addr):
		"""
		Converts a string of 6 characters of ethernet address
		into a dash separated hex string
		"""
		return ":".join(list("%.2x" % (ord(x)) for x in addr))


	def __parse_icmp_packet(self, packet, ip_header_length):
		"""
		Method to parse ICMP packet
		"""
		u = ip_header_length + self.ETH_HEADER_SIZE
		icmph_length = 4
		icmp_header = packet[u:u+4]

		icmph = unpack('!BBH' , icmp_header)
		icmp_type, code, checksum = icmph[0], icmph[1], icmph[2]

		h_size = self.ETH_HEADER_SIZE + ip_header_length + icmph_length
		data_size = len(packet) - h_size

		data = packet[h_size:]


	def __parse_tcp_packet(self, packet, ip_header_length):
		"""
		Method to parse TCP packet
		"""
		t = ip_header_length + self.ETH_HEADER_SIZE
		tcp_header = packet[t:t+20]

		tcph = unpack('!HHLLBBHHH' , tcp_header)

		source_port = tcph[0]
		dest_port = tcph[1]
		sequence = tcph[2]
		acknowledgement = tcph[3]
		doff_reserved = tcph[4]
		tcph_length = doff_reserved >> 4

		"""
		print 'Source Port : ' + str(source_port) + \
			   ' Dest Port : ' + str(dest_port) + \
			   ' Sequence Number : ' + str(sequence) + \
			   ' Acknowledgement : ' + str(acknowledgement) + \
			   ' TCP header length : ' + str(tcph_length)
		"""

		h_size = self.ETH_HEADER_SIZE + ip_header_length + tcph_length * 4
		data_size = len(packet) - h_size

		data = packet[h_size:]


	def __parse_udp_packet(self, packet, ip_header_length, s_addr, d_addr, packet_ep_time):
		"""
		Method to parse UDP packet
		"""
		u = ip_header_length + self.ETH_HEADER_SIZE
		udph_length = 8
		udp_header = packet[u:u+8]

		udph = unpack('!HHHH' , udp_header)

		source_port = udph[0]
		dest_port = udph[1]
		length = udph[2]
		checksum = udph[3]

		if (s_addr == sys.argv[2]) and (dest_port == 7078) and (length == 180):
			print 'UDP - Source Port : ' + str(source_port) + \
				  ' Dest Port : ' + str(dest_port) + \
				  ' Length : ' + str(length) + \
				  ' Checksum : ' + str(checksum)
			h_size = self.ETH_HEADER_SIZE + ip_header_length + udph_length
			data_size = len(packet) - h_size

			data = packet[h_size:]
			#print data.encode('hex')
			#print repr(data)
			data_hex = str(data.encode('hex'))
			data_hex_list = [data_hex[i:i+2] for i in range(0,len(data_hex), 2)]
			rtp_seq_hex = data_hex_list[2:4]
			rtp_sent_timestamp_hex = data_hex_list[4:8]
			#print rtp_seq_hex, rtp_sent_timestamp_hex
			rtp_seq = int("".join(str(y) for y in rtp_seq_hex),16)
			rtp_sent_timestamp = int("".join(str(y) for y in rtp_sent_timestamp_hex),16)
			print [rtp_seq, rtp_sent_timestamp, packet_ep_time]

			self.rtp_seq_list.append(rtp_seq)
			self.rtp_sent_timestamp_list.append(rtp_sent_timestamp)
			self.rtp_rec_time_list.append(packet_ep_time)

			packet_loss = 100.0*(1.0 - 1.0*len(self.rtp_seq_list)/(max(sorted(self.rtp_seq_list)) - min(sorted(self.rtp_seq_list)) + 1))
			print 'Packet Loss: ' + '{0:.2f}'.format(packet_loss) + '% (received ' + str(len(self.rtp_seq_list)) + ' of ' + str(max(sorted(self.rtp_seq_list)) - min(sorted(self.rtp_seq_list)) + 1) + ')\n'

			self.packet_loss_perc = packet_loss

			if (len(self.rtp_rec_time_list) >= 1):
				if (len(self.rtp_rec_time_list) == 1):
					delta_time = 0
					interarrival = 0
				else:
					delta_time = (packet_ep_time - self.rtp_rec_time_list[-2]) - (self.rtp_sent_timestamp_list[-1] - self.rtp_sent_timestamp_list[-2])*(1.0/8000)
					print packet_ep_time, self.rtp_rec_time_list[-2], self.rtp_sent_timestamp_list[-1], self.rtp_sent_timestamp_list[-2]
					print (packet_ep_time - self.rtp_rec_time_list[-2]), (self.rtp_sent_timestamp_list[-1] - self.rtp_sent_timestamp_list[-2])*(1.0/8000)
					delta_time = np.abs(delta_time)
					self.rtp_delta_list.append(delta_time)
					print 'Abs Delta: ' + '{0:.2f}'.format(delta_time*1000.0) + ' ms\n'
					print 'Max abs delta: ' + '{0:.2f}'.format(np.max(np.abs(self.rtp_delta_list))*1000.0) + ' ms\n'
					print 'Mean abs delta: ' + '{0:.2f}'.format(np.mean(np.abs(self.rtp_delta_list))*1000.0) + ' ms\n'

					interarrival = (packet_ep_time - self.rtp_rec_time_list[-2])
					interarrival = np.abs(interarrival)
					self.rtp_interarrival_list.append(interarrival)
					print 'Abs interarrival time: ' + '{0:.2f}'.format(delta_time*1000.0) + ' ms\n'
					print 'Max abs interarrival time: ' + '{0:.2f}'.format(np.max(np.abs(self.rtp_delta_list))*1000.0) + ' ms\n'
					print 'Mean abs innterarrival time: ' + '{0:.2f}'.format(np.mean(np.abs(self.rtp_delta_list))*1000.0) + ' ms\n'

				if (len(self.rtp_rec_time_list) == 1):
					jitter = 0
					jitter2 = 0
				else:
					jitter = self.rtp_jitter_list[-1] + (np.abs(delta_time) - self.rtp_jitter_list[-1])/16
					jitter2 = np.std(self.rtp_interarrival_list)
					#print np.abs(delta_time), self.rtp_rec_time_list[-1]
				self.rtp_jitter_list.append(jitter)
				print 'Jitter: ' + '{0:.2f}'.format(jitter*1000.0) + ' ms\n'
				print 'Max jitter: ' + '{0:.2f}'.format(np.max(self.rtp_jitter_list)*1000.0) + ' ms\n'
				print 'Mean jitter: ' + '{0:.2f}'.format(np.mean(self.rtp_jitter_list)*1000.0) + ' ms\n'

				self.jitter_ms = jitter*1000.0

				self.rtp_jitter2_list.append(jitter2)
				print 'Jitter2: ' + '{0:.2f}'.format(jitter2*1000.0) + ' ms\n'
				print 'Max jitter2: ' + '{0:.2f}'.format(np.max(self.rtp_jitter2_list)*1000.0) + ' ms\n'
				print 'Mean jitter2: ' + '{0:.2f}'.format(np.mean(self.rtp_jitter2_list)*1000.0) + ' ms\n'


			'''
			if (len(self.rtp_time_list) > 1):
				delta_time = packet_ep_time - self.rtp_time_list[-2]
				print '{0:.2f}'.format(delta_time*1000.0)
				self.rtp_delta_list.append(delta_time)
				jitter = np.std(self.rtp_delta_list)
				jitter2 = np.mean(np.abs([y - 0.002 for y in self.rtp_delta_list]))
				print 'Jitter: ' + '{0:.2f}'.format(jitter*1000.0) + ' ms\n'
				print 'Jitter2: ' + '{0:.2f}'.format(jitter2*1000.0) + ' ms\n'
				print 'Mean delta: ' + '{0:.2f}'.format(np.mean(self.rtp_delta_list)*1000.0) + ' ms\n'
			'''




	def __parse_ip_packet(self, packet, packet_ep_time):
		"""
		Method to parse IP packet
		"""
		ip_header = packet[self.ETH_HEADER_SIZE:self.IP_HEADER_SIZE+self.ETH_HEADER_SIZE]

		iph = unpack('!BBHHHBBH4s4s' , ip_header)

		version_ihl = iph[0]
		version = version_ihl >> 4
		ihl = version_ihl & 0xF

		iph_length = ihl * 4

		ttl = iph[5]
		protocol = iph[6]

		s_addr = socket.inet_ntoa(iph[8])
		d_addr = socket.inet_ntoa(iph[9])



		'''
		if s_addr == sys.argv[2]:
			print 'Version : ' + str(version) + \
				  ' IP Header Length : ' + str(ihl) + \
				  ' TTL : ' + str(ttl) + \
				  ' Protocol : ' + str(protocol) + \
				  ' Source Address : ' + str(s_addr) + \
				  ' Destination Address : ' + str(d_addr)
		'''

		if protocol == self.TCP_PROTOCOL_ID:
			#self.__parse_tcp_packet(packet, iph_length)
			pass
		elif protocol == self.ICMP_PROTOCOL_ID:
			#self.__parse_icmp_packet(packet, iph_length)
			pass
		elif protocol == self.UDP_PROTOCOL_ID:
			self.__parse_udp_packet(packet, iph_length, s_addr, d_addr, packet_ep_time)
		#else:
		#    print 'Protocol other than TCP/UDP/ICMP'


	def __parse_packet(self, packet, packet_ep_time):
		"""
		Method to parse a packet
		"""
		eth_header = packet[:self.ETH_HEADER_SIZE]
		eth = unpack('!6s6sH' , eth_header)
		eth_protocol = socket.ntohs(eth[2])
		"""
		print 'Destination MAC : ' + self.__conv_eth_addr(packet[0:6]) + \
			  ' Source MAC : ' + eth_addr(packet[6:12]) + \
			  ' Protocol : ' + str(eth_protocol)
		"""
		if eth_protocol == self.ETH_PROTOCOL_ID:
			self.__parse_ip_packet(packet, packet_ep_time)
		else:
			#print "Protocol other than ETH/IP"
			pass


	def latency_ms(self):
		r = pyping.ping(sys.argv[2],count=10, timeout=5000)
		return float(r.avg_rtt)/2

	def mos(self):
		eff_latency = np.mean(self.latency_ms_list) + self.jitter_ms*2 + 10
		if (eff_latency < 160):
			R = 93.2 - eff_latency/40.0
		else:
			R = 93.2 - (eff_latency-120)/10.0
		R = R - (self.packet_loss_perc*2.5)
		if R<0:
			MOS = 1
		elif R>100:
			MOS = 4.5
		else:
			MOS = 1 + 0.035*R + 0.000007*R*(R-60)*(100-R)
		return [R, MOS]

	def main(self, dev):
		#list all devices
		devices = pcapy.findalldevs()
		print devices

		#ask user to enter device name to sniff
		print "Available devices are :"
		for d in devices:
			print d

		#dev = raw_input("Enter device name to sniff : ")
		#dev = "eth0"

		print "Sniffing device " + dev

		'''
		open device
		# Arguments here are:
		#   device
		#   snaplen (maximum number of bytes to capture _per_packet_)
		#   promiscious mode (1 for true)
		#   timeout (in milliseconds)
		'''
		cap = pcapy.open_live(dev, 65536, 1, 0)
		dumper = cap.dump_open('temp.pcap')
		#print 'Before Latency:' + str(time.time())
		self.latency_ms_list.append(self.latency_ms())
		#print 'After Latency:' + str(time.time())

		#start sniffing packets
		while(True) :
			(header, packet) = cap.next()
			dumper.dump(header, packet)
			#print dir(header)
			#print "TIME: %s" % (str(header.getts()))
			#print ('%s: captured %d bytes, truncated to %d bytes' %(datetime.datetime.now(), header.getlen(), header.getcaplen()))

			packet_ep_time = time.time()
			if (len(self.rtp_rec_time_list) > 1):
				#print packet_ep_time, self.rtp_rec_time_list[-1]
				if np.abs(packet_ep_time - self.rtp_rec_time_list[-1]) > 10:
					#break
					#print 'Before Latency:' + str(time.time())
					self.latency_ms_list.append(self.latency_ms())
					#print 'After Latency:' + str(time.time())
					mos = self.mos()
					print 'Packet Loss (%): '+ str(self.packet_loss_perc)
					print 'Latency (ms): '+ str(np.mean(self.latency_ms_list))
					print 'Jitter (ms): ' + str(self.jitter_ms)
					print 'R = ' + str(mos[0])
					print 'e-MOS = ' + str(mos[1])
					return [self.packet_loss_perc, np.mean(self.latency_ms_list), self.jitter_ms, mos[0], mos[1]]

			self.__parse_packet(packet, packet_ep_time)

		#return


if __name__ == "__main__":
	VoipPacketCapture().main(sys.argv[1])
