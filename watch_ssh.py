import inotify.constants, inotify.adapters
import gpiozero as gpio
from re import search
import logging, sys
from logging.handlers import RotatingFileHandler

#Run the following command to gain control over led:  echo gpio | sudo tee /sys/class/leds/led0/trigger

LOG_PATH="/var/log/iaq/watch.log"
FILE_PATH="/var/log/auth.log"

def numberOfSSHOpen(filePath):
	n=0
	try:
		f = open(filePath, "r")
	except:
		logging.error("Failed to open the file")
		return -1
	for line in reversed(list(f)):
		if search("\]: New seat seat0", line):			# when last booted
			logging.debug(line.splitlines())
			break
		if search("\(sshd:session\): session opened for", line):
			logging.debug(line.splitlines())
			n=n+1
		elif search("\(sshd:session\): session closed for", line):
			logging.debug(line.splitlines())
			n=n-1
	f.close()
	logging.debug("Number of clientes connected: %d" % n)
	return n

def updateLed(led, numberOfConnections):
	if numberOfConnections>0:
		led.blink(0.2, 0.2, 7, background=False)
		led.on()
	elif numberOfConnections==0:
		led.off()

def _main():
	logging.basicConfig(handlers=[RotatingFileHandler(LOG_PATH, maxBytes=100000, backupCount=1)], format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S', level=logging.INFO)

	led = gpio.LED(47, active_high=False)
	nClients = numberOfSSHOpen(FILE_PATH)
	updateLed(led, nClients)

	i = inotify.adapters.Inotify()
	mask = inotify.constants.IN_CREATE | inotify.constants.IN_MODIFY | inotify.constants.IN_DELETE | inotify.constants.IN_DELETE_SELF | inotify.constants.IN_MOVED_FROM | inotify.constants.IN_MOVED_TO
	i.add_watch(FILE_PATH, mask)

	for event in i.event_gen(yield_nones=False):
		if 'IN_MODIFY' in event[1]:
			logging.debug("File was modified")
			n = numberOfSSHOpen(FILE_PATH)
			if n != nClients:
				updateLed(led, n)
			nClients = n
			logging.info("There are %d clients conected" % n)

		elif 'IN_DELETE' in event[1]:
			logging.critical("File was delete!!!")
			led.blink(0.1, 0.1, 20)
			led.on()
			sys.exit(0)

		else:
			(_, type_names, path, filename) = event
			logging.debug("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(path, filename, type_names))

if __name__ == '__main__':
	_main()
